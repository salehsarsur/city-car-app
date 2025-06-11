import bcrypt

new_pass = input("Enter new passcode: ")
hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt())
print(f"PASSCODE_HASH={hashed.decode()}")
