# 📁 Project Structure

```
movie-recommender/
│
├── 📱 app/                          # Next.js 14 App Router
│   ├── layout.tsx                   # Root layout (fonts, metadata)
│   ├── page.tsx                     # Main home page
│   └── globals.css                  # Global styles & animations
│
├── 🎨 components/
│   ├── sections/                    # Page-level components
│   │   ├── navbar.tsx              # Sticky glassmorphism navbar
│   │   ├── hero-section.tsx        # Full-screen cinematic hero
│   │   ├── search-modal.tsx        # Instant search (Cmd+K)
│   │   └── movie-detail-modal.tsx  # Movie details + recommendations
│   │
│   └── ui/                          # Reusable UI components
│       ├── movie-card.tsx          # Hover effects, optimized images
│       └── movie-row.tsx           # Horizontal scrollable carousel
│
├── 🔧 lib/
│   ├── api.ts                       # Typed API client + session mgmt
│   └── utils.ts                     # Helper functions (debounce, cn, etc)
│
├── 🪝 hooks/
│   └── useSessionTracking.ts        # Session ID + event tracking
│
├── 📝 types/
│   └── api.ts                       # TypeScript interfaces
│
├── ⚙️ Configuration Files
│   ├── package.json                 # Dependencies
│   ├── tsconfig.json               # TypeScript config
│   ├── tailwind.config.ts          # Tailwind theme + animations
│   ├── postcss.config.js           # PostCSS config
│   ├── next.config.js              # Next.js config (image domains)
│   ├── .env.local.example          # Environment template
│   └── .gitignore                  # Git ignore rules
│
└── 📚 Documentation
    ├── README.md                    # Full project documentation
    ├── QUICKSTART.md               # 5-minute setup guide
    └── docs/
        └── API.md                   # API integration guide

```

## Component Hierarchy

```
App (layout.tsx)
└── Home (page.tsx)
    ├── Navbar
    │   └── SearchButton → opens SearchModal
    │
    ├── HeroSection
    │   ├── Background Image
    │   ├── Movie Info
    │   └── CTA Buttons → open MovieDetailModal
    │
    ├── MovieRow (Trending)
    │   └── MovieCard[] → click opens MovieDetailModal
    │
    ├── MovieRow (Popular)
    │   └── MovieCard[]
    │
    ├── MovieRow (Top Rated)
    │   └── MovieCard[]
    │
    ├── SearchModal (conditional)
    │   ├── Search Input (debounced)
    │   └── Results[] → click opens MovieDetailModal
    │
    └── MovieDetailModal (conditional)
        ├── Movie Info
        ├── Like/Dislike Buttons → track events
        └── Recommendations[] → click opens new modal
```

## Data Flow

```
User Action → Component → API Client → Backend
                ↓
           State Update
                ↓
          UI Re-render
```

### Example: Movie Click Flow

```
1. User clicks MovieCard
   ↓
2. app/page.tsx: handleMovieClick()
   ↓
3. useSessionTracking: trackEvent("click")
   ↓
4. lib/api.ts: POST /events
   ↓
5. setSelectedMovieId(movie.id)
   ↓
6. MovieDetailModal renders
   ↓
7. lib/api.ts: GET /movie/{id}
   ↓
8. lib/api.ts: POST /events ("impression")
   ↓
9. lib/api.ts: GET /recommend/tfidf
   ↓
10. Display movie + recommendations
```

## State Management

### Client State (useState)
- `heroMovie`: Featured movie for hero section
- `trendingMovies`: Array of trending movies
- `popularMovies`: Array of popular movies
- `topRatedMovies`: Array of top rated movies
- `isSearchOpen`: Search modal visibility
- `selectedMovieId`: Currently viewed movie in modal
- `query`: Search input value
- `results`: Search results
- `liked`: User's like/dislike state

### Persistent State (localStorage)
- `movie_session_id`: Unique user session UUID

## Styling Architecture

### Tailwind Configuration
```
cinema-black (#050505)    → Body background
cinema-darker (#0a0a0a)   → Subtle variation
cinema-dark (#111111)     → Cards, modals
cinema-gray (#1a1a1a)     → Placeholder backgrounds
cinema-accent (#e50914)   → CTAs, highlights
cinema-gold (#f5c518)     → Star ratings
```

### Animation System
- **Framer Motion**: Component animations, page transitions
- **Tailwind**: Utility classes for simple animations
- **CSS**: Custom keyframes for shimmer effects

## File Sizes (Approximate)

```
app/page.tsx              ~3 KB
components/sections/*     ~12 KB total
components/ui/*           ~5 KB total
lib/api.ts                ~3 KB
Total Components          ~25 KB (before minification)
```

## Dependencies

### Production
```json
{
  "next": "14.2.15",           // React framework
  "react": "^18.3.1",          // UI library
  "react-dom": "^18.3.1",      // DOM renderer
  "framer-motion": "^11.11.7", // Animations
  "lucide-react": "^0.263.1"   // Icons
}
```

### Development
```json
{
  "@types/node": "^20",
  "@types/react": "^18",
  "@types/react-dom": "^18",
  "autoprefixer": "^10.4.20",
  "postcss": "^8.4.49",
  "tailwindcss": "^3.4.15",
  "typescript": "^5"
}
```

## Performance Optimizations

1. **Next.js Image**: Automatic optimization, lazy loading
2. **Code Splitting**: Automatic by Next.js App Router
3. **Debouncing**: Search input (300ms delay)
4. **Lazy Imports**: Modal components load on demand
5. **CSS-in-JS**: Zero runtime with Tailwind
6. **Tree Shaking**: Unused code eliminated in build

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile Safari (iOS 12+)
- Chrome Mobile (Android 5+)

## Accessibility Features

- Semantic HTML (`nav`, `main`, `section`)
- ARIA labels on icon buttons
- Keyboard navigation (Cmd/Ctrl+K, Escape)
- Focus indicators (custom ring styles)
- Alt text on all images
- Color contrast (WCAG AA compliant)

---

**Total Lines of Code**: ~2,000
**Components**: 9
**Hooks**: 1
**API Endpoints**: 5
**Setup Time**: 5 minutes
