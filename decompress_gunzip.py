import gzip

with gzip.open("NSE.json.gz", "rb") as f_in, open("NSE.json", "wb") as f_out:
    f_out.write(f_in.read())

print("✅ Decompressed to NSE.json")