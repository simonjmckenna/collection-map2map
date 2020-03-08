###############################################################################
#
# ollection.py - code to translate a apple maps collection to a google maos
#                compatible csv format. First produced to support ipace 
#                charging maps produced on Apple maps for Android users
#
#                developed by %1mes (from the ipaceforum.co.uk)                
#
#                              version 0.3
#
##############################################################################
import sys, struct, base64, urllib.parse

tempfile="/tmp/decoded_data"

class  entryData:
     st_valid=0
     name =''
     lat = 0.0
     lon = 0.0
     identifier=''
     def __init__(self):
         name="none"
         valid = 0
     def invalid(self):
         self.st_valid=0
         
     def valid(self):
         self.st_valid=1
         
     def isvalid(self):
         return self.st_valid
         
############################################################################

class collBlock:
     block=bytearray(0)
     length=0
     offset=0

     def __init__ (self):
         self.length=0
         self.offset=0
     
     def atend(self):
         if self.offset == self.length:
            return 1
         return 0
     
     def seek(self,change):
         if change > 0:
            self.offset += change
            if (self.offset > self.length):
                self.offset = self.length
         else:
            self.offset += change
            if (self.offset < 0): 
                self.offset = 0
                
     def load(self,f):
         blksz=bytes(1)
         blksz=f.read(1)
         self.length=blksz[0]
         # take a look at he nex byte - is it padding
         byte=f.read(1)
         while byte[0] == 1:
            print("INFORM have padding byte")
            byte=f.read(1)
         # goo back 1 - as we want to copy pass this one back  
         f.seek(-1,1)
         self.block=f.read(blksz[0])
         self.offset=0

     def read(self,count):
         # if not initialiised
         if self.length == 0:
            print ("ERROR read past end of collBlock")
            return ''
         # if this was falling off the end of the collblock shorten it
         if self.offset + count > self.length:
            count = self.length - self.offset
         # create the target buffer
         buffer=bytearray(count)
         #loop to copy the buffer in 
         x =0
         while x < count:
             buffer[x] = self.block[self.offset+x] 
             x+=1 
         # move th eposition counter forard
         self.offset += x
         return buffer

############################################################################

class collection:
      outputList = []
      fieldList= []
      numfields =0
      entry =0
      name = ''

      def __init__(self):
         self.name=''
         numfields=0
         entry=0
############################################################################

def extract_double(thisBlock):
    fpdata= bytearray(8)
    for x in range(8):
        fpdata[x] = thisBlock.read(1)[0]
    value = str(struct.unpack('d',fpdata)[0])
    return value

def process_textblock(thisBlock,size):
    txt = []

    if size == -1:
       size =0
       detail=1
    else:
       detail=0

    if size == 0:
       size = thisBlock.read(1)[0]
    #if thisBlock.offset + size > thisBlock.length:
    #   size = thisBlock.length - thisBlock.offset
    #   print ("trying to copy too many bytes")
    if detail == 1:
       print ("process_textblock:  block is "+str(size)+" bytes")

    i = 0
    while i < size:
        if thisBlock.atend():
            print("attempt to read past end of block")
        byte = thisBlock.read(1)
        if byte[0] == 0xe2:
           if detail == 1:
              print ("process_textblock: have special characters")
           # have  an odd bit of data in th emidle of a printble string
           thisBlock.seek(2)
           txt.append('-')
           byte = thisBlock.read(1)
           i += 3
        txt.append(chr(byte[0]))
        i += 1
    if detail == 1:
       print ("process_textblock: "+''.join(txt))
       
    return ''.join(txt)

def collection_name(thisBlock):
     name=process_textblock(thisBlock,thisBlock.length)
     print ("collection name: ",name)
     return name
     
def entry_data(thisBlock):
     # data block contains and identifier and some data
     thisEntry= entryData()
     while thisBlock.atend() == 0:
         got_entry=0
         entry_type=thisBlock.read(1)

         #we have an entry_idetifier        
         if entry_type[0] == 0x1a:
             thisEntry.identifier = process_textblock(thisBlock,0)
             thisEntry.valid()
             got_entry =1

         # Entry is latitude/longditude
         if entry_type[0] == 0x22:
             length = thisBlock.read(1)
             latcode = thisBlock.read(1) 
             if latcode[0] != 0x09:
                print ("Expected latitude code (0x09) got ["+str(latcode[0])+"].")
             thisEntry.lat = extract_double(thisBlock)
             loncode = thisBlock.read(1) 
             if loncode[0] != 0x11:
                print ("Expected lonitude code (0x11) got ["+str(loncode[0])+"].")
             thisEntry.lon = extract_double(thisBlock)
             thisEntry.valid()
             got_entry =1

         # Entry is latitude/longditude
         if entry_type[0] == 0x2a:
             thisEntry.name = process_textblock(thisBlock,0)
             got_entry =1 
             thisEntry.valid()
         # didnt find a known one 
         if got_entry == 0:
             print ("WARNING unknown block field entry initial key =["+str(entry_type[0])+"] len ["+str(thisBlock.length)+"].")
             thisEntry.invalid()
             return thisEntry
     return thisEntry



def decodeCollection(filename,my_collection):
    my_collection.entry=1 
    byte=bytes(1) 
    with open (filename, "rb") as f: 
        byte = f.read(1)
        thisBlock = collBlock()
        #collection name
        if byte[0] == 0x0a:
           thisBlock.load(f)
           my_collection.name=collection_name(thisBlock)
           got_name= 1
        else:
           print ("No collection Name found")
           got_name=0

        if got_name == 1:
           byte = f.read(1)
           while byte:
               got_block=0
               # Loop until we get t the end if we find a block header process it
               if byte[0]== 0x12:
                  thisBlock.load(f)
                  thisEntry = entry_data(thisBlock)
                  if thisEntry.isvalid() == 1:
                     buildMyCollection(thisEntry,my_collection)
                  got_block=1
               if got_block == 0:
                  print("WARNING Unknown block header ["+str(byte[0])+"].")
               byte = f.read(1)
    f.close()
    print ("Loaded "+str(my_collection.entry)+" entries.")
    return 

def buildMyCollection(thisEntry, my_collection):
    output= thisEntry.name + "," + thisEntry.lat + "," + thisEntry.lon + "," + thisEntry.identifier 
    numfields= output.count(',') + 1
    if numfields > my_collection.numfields:
       my_collection.numfields = numfields
    my_collection.outputList.append(output)
    my_collection.fieldList.append(numfields)
    my_collection.entry +=1

def writetofile(filename, data):
    o = open(filename,"wb")
    o.write(data)
    o.close
    return 1

def unpackStdinToFile(tempfile):
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

def buildHeader(fields):
    columns=[]
    if fields > 6 :
       columns.append("Name")
       columns.append("Lat")
       columns.append("Lon")
       # fill up with as many address fields as required
       for field in range (fields -6):
          columns.append("Address" + str(field+1))
       # Add the last 3 fields
       columns.append("Town")
       columns.append("Postcode")
       columns.append("Country")

       heading=""
       x=1
       # add each column title separeated by a comma
       for field in columns:
           heading +=field
           if x < fields: 
              heading+=','
           x+=1
       # Add the newline 
       heading+='\n'

       return heading

    print("we only have ", fields," fields in the data - this is not enough")
    sys.exit()

def buildEntries(my_collection):
    entries=[]
    x =0
    for entry in my_collection.outputList:
        # check to see if there are enough fields if not add some
        if my_collection.fieldList[x] < my_collection.numfields:
           recordlen = len(entry)

           # if we just have name and lat/lon
           if my_collection.fieldList[x] == 4:
               outdata=entry + ',' * ( my_collection.numfields - my_collection.fieldList[x])
           else:
             i=0
             commas=0
             outdata=''
             # scn the record esuring that we have the right number of fields (padded in the right place)
             while i < recordlen:
                if entry[i] == ',':
                   commas += 1
                  
                   if commas == (my_collection.fieldList[x] - 3):
                      # Add the number f fields we are short
                      outdata += ',' * ( my_collection.numfields - my_collection.fieldList[x])
                outdata += entry[i]
                i += 1

           # store the changed data
           entries.append(outdata+"\n")
        else:
           # didnt need to change anything store the original
           entries.append(entry+"\n")
        # move on to the next entry
        x+=1
    return entries

def processCollection(my_collection):
    entries = []

    header=buildHeader(my_collection.numfields)

    entries = buildEntries(my_collection)

    outputFile=my_collection.name.replace(" ","_")+".csv"   
    print ("writing to: ",outputFile)

    o = open(outputFile,"wt")

    o.write(header)
    e = 1
    for entry in entries:
       o.write(entry)
       e+=1 

    o.close()

    print("Written "+str(e)+" entries.")
    

#
# Core of program
#

unpackStdinToFile(tempfile)
my_collection = collection()
decodeCollection(tempfile,my_collection)
processCollection(my_collection)
