# collection-map2map
Code to translate an Apple Maps collection (stored as data in an URL) to google maps data (CSV format)

This is a piece of python code (apologies I'm using this as part of an exercise to learn a bit of python - so my python code will not be brilliant) that turns the encoded Apple maps collection data (stored in the URL) into a CSV file that can be used by google maps as input data.

The collection data is shared as a URL with all the colelction data as a veriable "_col" in that URL. 

 href="https://collections.apple.com/collection?_col=Cg1Hb29kIENoY...YhDMAqF1RodXJzbyBDUFMgKFBhcmsgSG90ZWwp"
 
 The data is URL encoded (spaces mapped to %20, = mapped to %3D etc), then it's base64 encoded. 
 
 The resulting binary file contains the collection data (collection name) then a sequence of records - one for each collection entry. 
 
 Text fields are a number of bytes with the first byte defining the field length.
 lat/lon are stored as an 8 byte double. 
 
 Each record starts with a name, then an address field, then lat and long. There are various bytes of field identifiers, and a small amount of data I havent identified as yet.
 
The script currently

1) decodes the file to it's binary format - storing it on disk (the source data is passed in on stdin) 
2) loads the file in byte by byte and parses it. 
3) creates a csv file named for the collection 
4) produces a header row Name, lat, Lon, A variable number of address fields - constant for the collection (google maps likes this to be consistent) town, postcode and country. 
5) writes a line per collection entry padding the address field as required in csv format.

This CSV file can then be loaded as a layer in google maps. 
