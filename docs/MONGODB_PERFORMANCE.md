# MongoDB High-Performance & Asynchronous Architecture Guide
## (মঙ্গোডিবি হাই-পারফরম্যান্স ও অ্যাসিনক্রোনাস আর্কিটেকচার গাইডলাইন)

MongoDB-তে ডাটা যখন কয়েক লাখ (যেমন: ২-৩ লাখ বা মিলিয়ন) হয়ে যায়, তখন সঠিক অপ্টিমাইজেশন ও অ্যাসিনক্রোনাস আর্কিটেকচার না থাকলে কোয়েরি স্লো হয়ে যায়। নিচে প্রধান সমস্যাগুলো এবং সেগুলোর চূড়ান্ত প্রতিকার ও স্ট্যান্ডার্ড কোড প্যাটার্ন দেওয়া হলো।

> [!IMPORTANT]
> **Native Async PyMongo vs Motor Architecture**:
> For the complete architectural analysis of PyMongo 4.9+ native `AsyncMongoClient`, Motor deprecation roadmap, Beanie ODM vs Raw Async, and PostgreSQL comparison, refer to [docs/ASYNC_MONGODB_PRODUCTION_GUIDE.md](file:///c:/Users/Sourav/Documents/Start/docs/ASYNC_MONGODB_PRODUCTION_GUIDE.md).

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

---

## ৩. পপুলেশন বা জয়েন ($lookup / fetch_links) ট্র্যাপ ও ৩টি বিস্ট-মোড টেকনিক
### সমস্যা:
অন্ধভাবে `fetch_links=True` বা সাধারণ `$lookup` চালালে MongoDB পুরো লিঙ্কড ডকুমেন্ট (পাসওয়ার্ড, সেটিংস, হেভি অ্যারে) টেনে আনে, যা মেমোরি শেষ করে সার্ভার ১০ গুণ স্লো করে দেয়।

### সমাধান ও স্ট্যান্ডার্ড:

#### টেকনিক ১: সাব-পাইপলাইন ও প্রজেকশন সহ $lookup (Production-Grade $lookup)
প্রথমে ইনডেক্সড ফিল্ড দিয়ে `$match` এবং `$limit` করে ডেটাসেট ছোট করুন, তারপর `$lookup`-এর ভেতর `pipeline` দিয়ে শুধু দরকারি ২-৩টি ফিল্ড প্রজেক্ট করুন:
```python
pipeline = [
    # ১. প্রথমেই ফিল্টার ও লিমিট (লাখ লাখ ডেটা জয়েন হওয়া বন্ধ করবে)
    {"$match": {"status": "completed"}},
    {"$sort": {"createdAt": -1}},
    {"$limit": 20},
    # ২. সাব-পাইপলাইন দিয়ে শুধু দরকারি ফিল্ড প্রজেক্ট
    {
        "$lookup": {
            "from": "users",
            "localField": "userId",
            "foreignField": "_id",
            "as": "user",
            "pipeline": [{"$project": {"_id": 0, "name": 1, "email": 1}}],
        }
    },
    {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
]
```

#### টেকনিক ২: অ্যাপ্লিকেশন-লেভেল ব্যাচ পপুলেশন ($in Query — Mongoose স্টাইল)
কমপ্লেক্স জয়েনের বদলে পাইথনে দুটি ইনডেক্সড কোয়েরি চালিয়ে ইন-মেমোরি ডিকশনারিতে ম্যাপ করা আরও বেশি ফাস্ট:
```python
# কুয়েরি ১: লিমিটেড ডেটা ফেচ (১ms)
orders = await Order.find(Order.status == "completed").limit(20).to_list()
user_ids = list({o.userId for o in orders if o.userId})

# কুয়েরি ২: Primary Index _id দিয়ে একক $in ফেচ (১ms)
users = await User.find({"_id": {"$in": user_ids}}).project(UserShortView).to_list()
user_map = {u.id: u for u in users}

# পাইথন মেমরিতে ০.০১ মিলিসেকেন্ডে ম্যাপিং (ডাটাবেসে জয়েন জিরো!)
return [{**o.model_dump(), "user": user_map.get(o.userId)} for o in orders]
```

#### টেকনিক ৩: এক্সটেন্ডেড রেফারেন্স প্যাটার্ন (Extended Reference Pattern — 0 Join!)
হাই-স্কেল সিস্টেমে (১০,০০০+ RPS) কোনো জয়েন না করে ডকুমেন্টের ভেতরই প্রয়োজনীয় তথ্যের ছোট স্ন্যাপশট এমবেড করে রাখা হয়:
```json
{
  "_id": "order_101",
  "amount": 250,
  "buyer": { "userId": "u_1", "name": "Sourav", "avatar": "https://..." }
}
```
একটিমাত্র কোয়েরিতে ০.৫ মিলিসেকেন্ডে পেজের সব ডেটা চলে আসে। ইউজার প্রোফাইল চেঞ্জ করলে ব্যাকগ্রাউন্ড টাস্কে অ্যাসিঙ্ক আপডেট করা হয়।

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
