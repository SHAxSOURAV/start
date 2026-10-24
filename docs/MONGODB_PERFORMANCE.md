# MongoDB High-Performance & Asynchronous Architecture Guide
## (মঙ্গোডিবি হাই-পারফরম্যান্স ও অ্যাসিনক্রোনাস আর্কিটেকচার গাইডলাইন)

MongoDB-তে ডাটা যখন কয়েক লাখ (যেমন: ২-৩ লাখ বা মিলিয়ন) হয়ে যায়, তখন সঠিক অপ্টিমাইজেশন ও অ্যাসিনক্রোনাস আর্কিটেকচার না থাকলে কোয়েরি স্লো হয়ে যায়। নিচে প্রধান সমস্যাগুলো এবং সেগুলোর চূড়ান্ত প্রতিকার ও স্ট্যান্ডার্ড কোড প্যাটার্ন দেওয়া হলো।

---

## ১. সঠিক ইনডেক্সিং (Indexing) - COLLSCAN প্রতিরোধ ও IXSCAN নিশ্চিতকরণ
### সমস্যা:
ইনডেক্স ছাড়া MongoDB পুরো কালেকশন স্ক্যান করে (Collection Scan বা `COLLSCAN`)। ২-৩ লাখ ডকুমেন্ট থাকলে প্রতি কোয়েরিতে লক্ষ লক্ষ রেকর্ড স্ক্যান করতে হয়, যা সিপিইউ এবং মেমোরিতে তীব্র জট তৈরি করে।

### সমাধান ও স্ট্যান্ডার্ড:
1. **রেগুলার ফিল্টার/সার্চ ফিল্ডে ইনডেক্স**: যে ফিল্ডগুলোতে নিয়মিত `find`, `match`, `sort` বা `$lookup` হয়, সেগুলোতে অবশ্যই ইনডেক্স নিশ্চিত করতে হবে:
   ```python
   import pymongo
   from beanie import Document


   class User(Document):
       email: str
       authId: PydanticObjectId
       isDeleted: bool = False
       deletedAt: datetime | None = None

       class Settings:
           name = "users"
           indexes = [
               pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
               pymongo.IndexModel([("authId", pymongo.ASCENDING)]),
               # Compound Index for Soft Delete & Filter
               pymongo.IndexModel(
                   [("isDeleted", pymongo.ASCENDING), ("deletedAt", pymongo.ASCENDING)]
               ),
           ]
   ```
2. **Compound Indexes**: একাধিক ফিল্ড দিয়ে ফিল্টার ও সর্ট করার ক্ষেত্রে কম্পাউন্ড ইনডেক্স ব্যবহার করতে হবে। যেমন: `[("status", 1), ("createdAt", -1)]`।
3. **Execution Stats চেক**: স্লো কোয়েরি চেক করতে `.explain("executionStats")` চালিয়ে নিশ্চিত হতে হবে যে `stage` যেন `IXSCAN` (Index Scan) হয়, কখনোই `COLLSCAN` নয়।

---

## ২. লার্জ ডেটা ফেচ ও পেজিনেশন (Cursor-based Pagination vs Skip)
### সমস্যা:
একসাথে হাজার হাজার রেকর্ড মেমোরিতে আনা এবং বড় `skip` (যেমন: `skip(100000).limit(20)`) ব্যবহার করলে MongoDB আগের ১ লাখ ডকুমেন্ট স্ক্যান করে ড্রপ করে, যা পারফরম্যান্স ধ্বংস করে দেয়।

### সমাধান ও স্ট্যান্ডার্ড:
1. **Strict Projections**: সবসময় প্রয়োজনীয় ফিল্ড সিলেক্ট করুন, অপ্রয়োজনীয় ডাটা (যেমন: হেভি টেক্সট, পাসওয়ার্ড, বড় অ্যারে) ফেচ করবেন না:
   ```python
   # Beanie Projection
   user = await User.find_one(User.email == email).project(UserPublicView)
   # অথবা PyMongo driver-এ
   user = await User.get_pymongo_collection().find_one(
       {"email": email}, {"password": 0, "__v": 0}
   )
   ```
2. **Cursor-based (Keyset) Pagination**: অফসেট `skip`-এর বদলে লাস্ট আইটেমের `_id` বা `createdAt` ফিল্টার ব্যবহার করুন:
   ```python
   # Keyset pagination: O(1) time complexity even on millions of docs
   cursor = (
       User.get_pymongo_collection()
       .find({"_id": {"$gt": ObjectId(last_seen_id)}}, {"name": 1, "email": 1})
       .sort("_id", 1)
       .limit(20)
   )
   ```

---

## ৩. পপুলেশন বা জয়েন ($lookup) অপ্টিমাইজেশন ও Denormalization
### সমস্যা:
রিলেশনাল ডাটাবেসের মতো বারবার `$lookup` বা `.populate()` চালালে, বিশেষ করে বড় কালেকশন বা আন-ইনডেক্সড ফিল্ডে, কোয়েরি এক্সিকিউশন টাইম বহুগুণ বেড়ে যায়।

### সমাধান ও স্ট্যান্ডার্ড:
1. **Denormalization (Embedding)**: ঘন ঘন একসাথে প্রয়োজন হওয়া ছোট ও বাউন্ডেড ডাটা (যেমন: ইউজার কোঅর্ডিনেট, অ্যাড্রেস, স্ট্যাটাস) আলাদা কালেকশনে না রেখে প্যারেন্ট ডকুমেন্টে সরাসরি এমবেড করুন।
2. **$lookup-এর ক্ষেত্রে ইনডেক্সিং**: `$lookup` ব্যবহার করলে `localField` এবং `foreignField` উভয়টিতেই ইনডেক্স থাকতে হবে:
   ```python
   # localField: "authId", foreignField: "_id" -> ensure "authId" has an IndexModel
   ```
3. **প্রজেকশন সহ ছোট জয়েন**: জয়েন করার পরেই `$project` স্টেজ দিয়ে শুধু প্রয়োজনীয় কলামগুলো রাখুন।

---

## ৪. অ্যাসিনক্রোনাস লুপে N+1 কোয়েরি সমস্যা (Async/Await Pitfall)
### সমস্যা:
`for` লুপের মধ্যে প্রতিটি আইটেমের জন্য আলাদাভাবে `await Model.find_one(...)` চালালে সিকোয়েন্সিয়াল বটলনেক তৈরি হয়। ১০০টি আইটেমের জন্য ১০০টি নেটওয়ার্ক রাউন্ডট্রিপ অপেক্ষা করতে হয়।

### সমাধান ও স্ট্যান্ডার্ড:
1. **$in অপারেটর ব্যবহার করে একক কোয়েরিতে ফেচ**:
   ```python
   # FORBIDDEN (N+1 Anti-Pattern):
   # for uid in user_ids:
   #     user = await User.find_one({"_id": uid})

   # REQUIRED (Superfast Single Query):
   users = (
       await User.get_pymongo_collection()
       .find({"_id": {"$in": user_ids}})
       .to_list(length=len(user_ids))
   )
   ```
2. **প্যারালাল অ্যাসিনক্রোনাস ফেচ (`asyncio.gather`)**:
   যদি একাধিক স্বতন্ত্র কোয়েরি আলাদা কালেকশনে প্যারালালে চালাতে হয়:
   ```python
   user_task = User.find_one({"_id": user_id})
   orders_task = Order.find({"userId": user_id}).to_list()
   user, orders = await asyncio.gather(user_task, orders_task)
   ```

---

## ৫. আন-অপ্টিমাইজড এগ্রিগেশন পাইপলাইন (Pipeline Optimization)
### সমস্যা:
পাইপলাইনের শুরুতে `$lookup`, `$unwind` বা হেভি গ্রুপ অপারেশন চালালে মেমোরি লিমিট (১০০ এমবি) শেষ হয়ে যায় এবং সার্ভার ড্রপ করে।

### সমাধান ও স্ট্যান্ডার্ড:
1. **Pipeline Ordering**: পাইপলাইনের শুরুতেই সবসময় `$match` এবং `$sort` রাখুন যাতে মেমোরিতে প্রসেস করার আগেই ডেটাসেট ফিল্টার হয়ে ছোট হয়ে যায়:
   ```python
   pipeline = [
       # ১. প্রথমে ফিল্টার (ইন্ডেক্স ব্যবহার করে ছোট করা)
       {"$match": {"isActive": True, "isDeleted": False}},
       # ২. ইনডেক্সড সর্ট
       {"$sort": {"createdAt": -1}},
       # ৩. লিমিট (প্রয়োজনীয় সংখ্যক নেওয়া)
       {"$limit": 50},
       # ৪. এরপর শুধুমাত্র ৫০টি ডকুমেন্টের ওপর $lookup
       {
           "$lookup": {
               "from": "users",
               "localField": "authId",
               "foreignField": "_id",
               "as": "user_profile",
           }
       },
       # ৫. ফিল্ড প্রজেকশন
       {"$project": {"user_profile.name": 1, "email": 1, "createdAt": 1}},
   ]
   ```

---

## ৬. কানেকশন পুলিং (Connection Pooling)
### সমস্যা:
প্রতিটি রিকোয়েস্টে নতুন ডাটাবেস কানেকশন তৈরি করলে সকেট ও হ্যান্ডশেক ওভারহেডে সার্ভার স্লো হয়ে যায়।

### সমাধান ও স্ট্যান্ডার্ড:
1. `AsyncMongoClient`-এর সিঙ্গেলটন কানেকশন পুল ব্যবহার করুন (যা `src/connection/connect_db.py`-এ অলরেডি কনফিগার করা আছে: `maxPoolSize=50`, `minPoolSize=10`):
   ```python
   AsyncMongoClient(
       config.mongo_url,
       maxPoolSize=50,
       minPoolSize=10,
       maxIdleTimeMS=30000,
   )
   ```

---

## 🎯 চেকলিস্ট: প্রতিটি নতুন মডেল ও কুয়েরির জন্য
- [ ] যে ফিল্ডে ফিল্টার/সার্চ/সর্ট আছে, তাতে `pymongo.IndexModel` ডিফাইন করা হয়েছে?
- [ ] ফরেন কি রেফারেন্সে (যেমন: `authId`, `userId`) ইনডেক্স দেওয়া হয়েছে?
- [ ] কোয়েরিতে `AUTH_PUBLIC_PROJECTION` বা স্পেসিফিক প্রজেকশন ব্যবহার করা হয়েছে?
- [ ] লুপের ভেতর `await` দিয়ে একাধিক কোয়েরি না চালিয়ে `$in` বা ব্যাচিং ব্যবহার করা হয়েছে?
- [ ] সফট ডিলিটের ফিল্ডে `[("isDeleted", 1), ("deletedAt", 1)]` কম্পাউন্ড ইনডেক্স আছে?
