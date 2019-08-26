echo "Deleting file"
ampy rmdir Sources
echo "Uploading files"
sleep 1
ampy put Sources
#sleep 1
#echo "Running"
#ampy run main.py
echo "Done"
