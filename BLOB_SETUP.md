# Vercel Blob Storage Setup

This guide will help you migrate your JSON data files from local storage to Vercel Blob Storage.

## 🚀 Quick Setup

### 1. Create a Vercel Account & Project
1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Create a new project or use an existing one
3. Go to your project dashboard

### 2. Create a Blob Store
1. In your Vercel dashboard, go to **Storage** tab
2. Click **Create Database** → **Blob**
3. Give it a name like `financial-data-storage`
4. Click **Create**

### 3. Get Your Blob Token
1. In the Blob store dashboard, go to **Settings**
2. Copy the **BLOB_READ_WRITE_TOKEN**
3. This token allows read/write access to your blob store

### 4. Set Environment Variable
Create a `.env.local` file in your project root:

```bash
BLOB_READ_WRITE_TOKEN=your_token_here
```

**Important**: Add `.env.local` to your `.gitignore` to keep your token secure!

### 5. Upload Your Data Files
Run the upload script:

```bash
bun run upload-data
```

This will:
- Upload JSON files from `public/data/` to Blob Storage
- Generate public URLs for each file
- Display a URL mapping for easy integration

### 6. Update Your Code
After upload, verify `blob_mapping.json`. The dashboard fetches this mapping at runtime, so you do not need to hardcode per-file Yahoo URLs in `src/utils/dataLoader.ts`.

## 🔧 How It Works

### Before (Local Files)
```
/public/data/bubble_data_AAPL_splitadj_1996to2023.json
```

### After (Blob Storage)
```
https://your-blob-store.vercel-storage.com/bubble_data_AAPL_splitadj_1996to2023.json
```

### Runtime Mapping
The app reads `blob_mapping.json` from Blob Storage at runtime for the daily Yahoo dataset. Static WRDS assets remain separately configured.

### Incremental Uploads
The scheduled pipeline now avoids rewriting unchanged CSV and JSON files. It also skips the Vercel redeploy when no published Blob content changed, which reduces read/write usage over the month.

## 💰 Pricing
Vercel Blob Storage pricing (as of 2024):
- **Free tier**: 1GB storage, 100GB bandwidth
- **Pro**: $20/month for 100GB storage, 1TB bandwidth
- **Enterprise**: Custom pricing

Your JSON files are likely well within the free tier limits.

## 🔒 Security
- Blob URLs are public but unguessable (contain random tokens)
- Read-only access for your application users
- Write access only with your private token

## 🚀 Deployment
When deploying to Vercel:
1. Add `BLOB_READ_WRITE_TOKEN` to your Vercel project environment variables
2. Your app will automatically use Blob Storage URLs
3. Faster loading with global CDN distribution

## 📝 Next Steps
1. Follow the setup steps above
2. Run `bun run upload-data`
3. Update the URL mapping in your code
4. Test locally
5. Deploy to Vercel!
