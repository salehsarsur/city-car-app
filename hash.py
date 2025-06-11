import bcrypt

# Change this to your initial passcode
plain_passcode = b"admin123"

# Generate a bcrypt hash
hashed = bcrypt.hashpw(plain_passcode, bcrypt.gensalt())

# Print the result
print("Hashed passcode:")
print(hashed.decode())
