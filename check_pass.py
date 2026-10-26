import bcrypt

# আপনার config.yaml-তে থাকা niloy-এর হ্যাশ
hashed_from_yaml = b'$2b$12$DFMMAEtYsKjQTkkVBAWAOO8x4r6o2xyBNT9C19u2c8OJEp.CL1LQW'
# আপনি যে পাসওয়ার্ডটা দিচ্ছেন
password_to_test = b'niloy123'

if bcrypt.checkpw(password_to_test, hashed_from_yaml):
    print("✅ সফল! পাসওয়ার্ড এবং হ্যাশ একদম মিলেছে।")
else:
    print("❌ ব্যর্থ! পাসওয়ার্ড এবং হ্যাশ মিলছে না।")