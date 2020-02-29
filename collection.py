#
# Need to process max file first using sed t remove any URL % formatting 
#
# sed 's@+@ @g;s@%@\\x@g' <source file>  | xargs -0 printf "%b" | base64 -d > <output> 
#
#  then run python3 collection.py (this file) 
#


import sys
import struct
import base64
import urllib.parse

def readtextblock(len,f):
    txt = []
    i = 0
    while i < len:
      byte = f.read(1)
      if byte[0] == 0xe2:
          # get ridof the unrintable 3 char block (tbd figure out what this is
          byte = f.read(1)
          byte = f.read(1)
          if byte[0] == 0x93:
              txt.append('-')
              byte = f.read(1)
              i+=3
      txt.append(chr(byte[0]))
      i += 1
    return ''.join(txt)

def process_txtblock(f):
   len = f.read(1)
   if len [0] > 256 :
       # feels liek its too long
       print ("len too long");
   else :
       txt = readtextblock(len[0],f)
       return txt

def extract_double(buffer,offset):
    fpdata= bytearray(8)
    x = 0
    for x in range(8):
        fpdata[x] = buffer[x+offset]
    value = str(struct.unpack('d',fpdata)[0])
    return value

def process_address_data(f,collection_entry):
    buffer = bytes(18)
    buffer = f.read(18)
    # try to pull data out of the binary fields
    collection_entry['lat'] = extract_double(buffer,0)
    collection_entry['lon'] = extract_double(buffer,9)
    # read the address string 
    collection_entry['name'] = process_txtblock(f)
    return 1

def block_code(f, collection_entry):
    code = f.read(1)
    
    if code[0] == 0x09:
       process_address_data(f,collection_entry)
       # entry complete
       collection_entry['state'] = 3
    else : 
       # new entry
       collection_entry['state'] = 0
       
def entry_address(f, collection_entry):
    collection_entry['data'] = process_txtblock(f)#
    collection_entry['state'] = 2

def collection_name(f, collection_entry):
    filename = process_txtblock(f)#
    # remove any whitespace from collection name
    filename = filename.replace(" ","_")
    filename = filename + ".csv"
    collection_entry['file'] = filename
    collection_entry['state'] = 1


def block_head_parse(byte, collection_entry):
     ##print ("in block_head_parse [",byte[0],"][",byte,"]")
     switcher = {
         0x00: dummy,
         0x0a: collection_name,
         0x12: block_code,
         0x1a: entry_address,
         0xff: lambda f :'error'
     }
     func=switcher.get(byte[0],lambda f, collection_entry : "unknown block header" )
     return func(f, collection_entry)

def dummy(f):
     x=1


def writetofile(filename, data):
     o = open(filename,"wb") 
     o.write(data)
     o.close
     return 1

#Main block of code

def unpack_stdintofile(tempfile):
    # red the input from stdin, process it and write out to a temporary files, then process collection
    input_str = sys.stdin.read()
    print("read data from stdin")
    nonweb=urllib.parse.unquote(input_str)
    print("decoded URL in input data")
    # write the  url decided dat out to a file for diagnotics
    writetofile("/tmp/urldecoded",str.encode(nonweb))
    collection=base64.b64decode(nonweb)
    print("decoded base64 in input data")
    # open the tempfile and write it all out
    writetofile(tempfile,collection) 
    print("written decoded data to ",tempfile)
    return 1
     

tempfile="/tmp/decoded_data"
unpack_stdintofile(tempfile)
collection_output = []
# open the input as a bytestream
entries = 0
with open(tempfile, "rb") as f:
     #initialise collection_entry, read the first byte into the program
     collection_entry={ 'state': 0 , 'fields': 0 }
     byte = bytes(1)
     byte = f.read(1)
     # loop until we get to the end of the file
     while byte:
        # if we are not in a block - look for a master code
        # need to pass the data as disctionaries
        block_head_parse(byte,collection_entry)

        if collection_entry['state'] == 1:
            # Got a collection nme - need ot do a few things 
            #open outtut file
            o = open(collection_entry['file'],"w") 
              
        if collection_entry['state'] == 3:
            # we have a complete entry
            entrystring = collection_entry['name'] + "," + collection_entry['lat'] + "," + collection_entry['lon'] + ',' + collection_entry ['data'] + "\n"
            # Google maps is picky, it needs a constant number of columns - addresses dont do this..
            # how many columnns do we have in this line
            numfields=entrystring.count(',') + 1
            # if this is our new record - store it. 
            if collection_entry['fields'] < numfields:
               collection_entry['fields'] = numfields

            # got a complete entry - store the output until we are ready    
            collection_output.append(entrystring)
            entries += 1
            collection_entry['state'] = 0
        byte = f.read(1)

     # finished with the input file - close it
     f.close

     # finished loading the data in - now get ready to write it out..
     print ("Read data have " , entries , " records in collection ") 

     # whats th maximum number of fields in a record
     numfields =  collection_entry['fields']
     print ("numfields=",numfields)
     if numfields > 6 :
        columns = []
        columns.append("Name")
        columns.append("Lat")
        columns.append("Lon")
        # fill up with as many address fields as required
        for field in range (numfields -6): 
          columns.append("Address" + str(field+1))
        # Add the last 3 fields
        columns.append("Town")
        columns.append("Postcode")
        columns.append("Country")
     else:
         print ("We only have ", numfields," fields in the data - this is not enough")
         sys.exit()

     # Build the header string
     heading=""
     x=1
     for field in columns:
         heading += field 
         if x < numfields :
            heading += ","
         x += 1
     #Add newline
     heading += "\n"

     # write all the heading data out
     o.write(heading)
     # Go through each output lin  ensure we have enough fields pad if not
     # need to pad in the middle as it's in the address we will go wrong
     for outline in collection_output:
         fieldcount = outline.count(',') + 1
         if fieldcount < numfields:
            outlen = len(outline)
            i=0
            commas =0;
            outdata=''
            while i < outlen :
               outchar = outline[i]
               if outchar == ',':
                  commas += 1
                  # th last 3 fields are town,postcode,country - pad afte 4th comma
                  if commas == (fieldcount - 3):
                      # add a number of commas to the output string
                      outdata += ',' * (numfields - fieldcount)
               # append the caracter
               outdata += outchar
               i+=1
            #write the line
            o.write(outdata)
         else:
            # write the unmolested line out
            o.write(outline)

     # fiished close the file 
     o.close
