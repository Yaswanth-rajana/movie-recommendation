# 🎬 Cinematic - Movie Recommendation System

A stunning, production-ready movie recommendation frontend built with Next.js 14, featuring cinematic design, AI-powered personalization, and buttery-smooth animations.

![Next.js](https://img.shields.io/badge/Next.js-14-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-cyan)
![Framer Motion](https://img.shields.io/badge/Framer_Motion-11-pink)

## ✨ Features

### 🎨 **Cinematic Design**
- **Immersive Hero Section**: Full-screen backdrop with gradient overlays
- **Glassmorphism**: Stunning blur effects on navigation and modals
- **Micro-interactions**: Smooth hover effects, scale animations, and staggered reveals
- **Dark Theme**: Deep blacks (#050505) with rich gradients

### 🚀 **Core Functionality**
- **Smart Search**: Instant search with debouncing (Cmd/Ctrl + K)
- **Movie Discovery**: Trending, Popular, and Top Rated categories
- **Personalized Recommendations**: Content-based recommendations powered by your backend
- **Interactive Feedback**: Like/Dislike buttons with event tracking
- **Session Tracking**: UUID-based personalization stored in localStorage

### 🎯 **Performance**
- **Next.js 14 App Router**: Server components + client components
- **Optimized Images**: Next.js Image component with proper sizing
- **Lazy Loading**: Components load on demand
- **Smooth Animations**: 60fps animations with Framer Motion

## 🏗️ Architecture

```
movie-recommender/
├── app/
│   ├── layout.tsx          # Root layout with fonts
│   ├── page.tsx            # Main home page
│   └── globals.css         # Global styles
├── components/
│   ├── sections/
│   │   ├── navbar.tsx              # Sticky nav with glassmorphism
│   │   ├── hero-section.tsx        # Immersive hero banner
│   │   ├── search-modal.tsx        # Instant search modal
│   │   └── movie-detail-modal.tsx  # Movie details + recommendations
│   └── ui/
│       ├── movie-card.tsx          # Hover effects, optimized images
│       └── movie-row.tsx           # Horizontal scrollable rows
├── lib/
│   ├── api.ts              # Typed API client
│   └── utils.ts            # Helper functions
├── hooks/
│   └── useSessionTracking.ts       # Session management hook
└── types/
    └── api.ts              # TypeScript interfaces
```

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ and npm
- FastAPI backend running at `http://localhost:8000`

### Installation

1. **Navigate to the project**:
```bash
cd movie-recommender
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure environment**:
```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Run development server**:
```bash
npm run dev
```

5. **Open your browser**:
```
http://localhost:3000
```

## 🎨 Design Principles

### Typography
- **Display Font**: Bebas Neue (Bold, impactful headlines)
- **Body Font**: Inter (Clean, readable body text)

### Color Palette
```css
--cinema-black: #050505     /* Deep background */
--cinema-darker: #0a0a0a    /* Slightly lighter black */
--cinema-dark: #111111      /* Cards & modals */
--cinema-gray: #1a1a1a      /* Subtle elements */
--cinema-accent: #e50914    /* Netflix-inspired red */
--cinema-gold: #f5c518      /* Star ratings */
```

### Motion Design
- **Page Load**: Staggered fade-in animations (0.05s delay per item)
- **Hover**: Scale (1.05x) with smooth transitions
- **Modals**: Scale + fade with backdrop blur
- **Search**: Instant debounced results (300ms)

## 🔌 API Integration

### Endpoints Used
```typescript
GET /home?category={category}&limit=20
GET /search?query={q}&limit=20
GET /movie/{tmdb_id}
GET /recommend/tfidf?title={movie_title}&top_n=10&session_id={uid}
POST /events
```

### Event Tracking
The app automatically tracks:
- **impression**: Movie viewed in detail modal
- **click**: Movie card clicked
- **like**: User liked the movie
- **dislike**: User disliked the movie

## 🎯 Key Components

### HeroSection
Displays the top trending movie with:
- Full-screen backdrop
- Gradient overlays
- Title, rating, genres, overview
- Watch Now & More Info CTAs

### SearchModal
Instant search with:
- Debounced input (300ms)
- Movie poster previews
- Keyboard shortcuts (Cmd/Ctrl + K)

### MovieDetailModal
Complete movie information:
- Backdrop image
- Full metadata (rating, year, runtime, genres)
- Like/Dislike interactions
- "You Might Also Like" recommendations

### MovieRow
Horizontal scrollable carousel:
- Arrow navigation (hidden until hover)
- Smooth scroll behavior
- Responsive card sizing

## 🛠️ Customization

### Change API URL
Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

### Modify Colors
Edit `tailwind.config.ts`:
```typescript
colors: {
  cinema: {
    black: "#your-color",
    accent: "#your-accent",
  }
}
```

### Adjust Fonts
Edit `app/layout.tsx`:
```typescript
import { YourFont } from "next/font/google";
```

## 📱 Responsive Design

- **Mobile**: Single column, touch-optimized
- **Tablet**: 2-3 cards per row
- **Desktop**: Full cinematic experience

## 🚀 Production Build

```bash
npm run build
npm run start
```

## 📊 Performance Targets

- **Lighthouse Score**: 100 (Performance)
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Bundle Size**: Optimized with Next.js automatic code splitting

## 🎭 UX Features

1. **Session Persistence**: User preferences saved in localStorage
2. **Optimistic UI**: Instant feedback on interactions
3. **Error Handling**: Graceful fallbacks for missing images/data
4. **Loading States**: Skeleton screens and spinners
5. **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation

## 🔮 Future Enhancements

- [ ] User authentication
- [ ] Watchlist/favorites persistence
- [ ] Advanced filters (genre, year, rating)
- [ ] Collaborative filtering recommendations
- [ ] Video trailers integration
- [ ] Social sharing

## 📝 License

MIT License - feel free to use this in your own projects!

## 🙏 Acknowledgments

- **TMDB**: The Movie Database API for movie data
- **Framer Motion**: For incredible animation capabilities
- **Next.js Team**: For the amazing framework

---

Built with ❤️ using Next.js 14, TypeScript, and Tailwind CSS
