# 🚀 Quick Start Guide

Get your cinematic movie app running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd movie-recommender
npm install
```

This will install:
- Next.js 14.2.15
- React 18.3.1
- Framer Motion 11.11.7
- Lucide React (icons)
- TypeScript 5
- Tailwind CSS 3.4

## Step 2: Configure Environment

Create a `.env.local` file:

```bash
cp .env.local.example .env.local
```

Make sure your FastAPI backend is running at `http://localhost:8000`.

If your backend is at a different URL, update `.env.local`:
```
NEXT_PUBLIC_API_URL=http://your-backend-url:port
```

## Step 3: Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Step 4: Test the Features

### 🔍 Search
- Press `Cmd + K` (Mac) or `Ctrl + K` (Windows/Linux)
- Or click the search icon in the navbar
- Type a movie name and see instant results

### 🎬 Browse Movies
- Scroll through "Trending Now", "Popular", and "Top Rated" sections
- Click any movie card to see details

### ❤️ Interact
- Click "Like" or "Dislike" on movies (tracked to your session)
- View personalized recommendations in the detail modal

### 🎯 Personalization
- Your session ID is automatically generated and stored
- All interactions are tracked for personalized recommendations

## Troubleshooting

### API Connection Issues

**Error**: `Failed to load home data`

**Solution**: 
1. Verify FastAPI backend is running: `http://localhost:8000/docs`
2. Check CORS settings in your backend allow `http://localhost:3000`
3. Verify `.env.local` has the correct API URL

### Images Not Loading

**Error**: Images show "No Image" placeholder

**Solution**:
1. Check if your backend is returning valid `poster_url` and `backdrop_url`
2. Verify URLs are accessible (TMDB URLs should work automatically)
3. Check `next.config.js` has the correct image domains configured

### Build Errors

**Error**: `Module not found` or TypeScript errors

**Solution**:
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

## Production Deployment

### Build for Production

```bash
npm run build
```

### Run Production Server

```bash
npm start
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Add environment variable in Vercel dashboard:
```
NEXT_PUBLIC_API_URL=https://your-production-api.com
```

## Performance Tips

1. **Enable Image Optimization**: Already configured in `next.config.js`
2. **Use Static Generation**: Hero movie could be statically generated at build time
3. **API Caching**: Implement React Query or SWR for better caching
4. **Bundle Analysis**: Run `npm run build` to see bundle sizes

## Development Tips

### Hot Reload
Next.js automatically reloads when you save files. If it doesn't work:
```bash
# Restart dev server
Ctrl + C
npm run dev
```

### Type Checking
```bash
# Check TypeScript errors without building
npx tsc --noEmit
```

### Linting
```bash
npm run lint
```

## Next Steps

1. ✅ **Test all features** with real API data
2. 🎨 **Customize colors** in `tailwind.config.ts`
3. 🔧 **Add more categories** by modifying `app/page.tsx`
4. 📱 **Test responsive design** on mobile devices
5. 🚀 **Deploy to production**

## Need Help?

- Check the main `README.md` for detailed documentation
- Review component files for inline comments
- Test individual components in isolation

---

Happy coding! 🎬✨
