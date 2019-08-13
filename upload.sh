echo "Uploading files"
for filename in Sources/*.py; do
	basename=$(basename "$filename")
	echo "$basename"
	ampy put "$filename"
	sleep 1
done
