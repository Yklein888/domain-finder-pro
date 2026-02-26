# Domain Finder Pro - Frontend Dashboard

A modern, responsive web dashboard for managing domain investments and opportunities.

## Features

### 📊 Dashboard Overview
- **Total Domains Analyzed**: Live count of domains in database
- **Portfolio Stats**: Items, ROI potential, estimated value
- **Quick Stats**: Visual overview of key metrics

### ⭐ Top Opportunities
- View highest-scoring domains
- Filter by quality score
- Add domains to portfolio
- See estimated values and ROI potential
- Color-coded quality grades (A-F)

### 👝 Portfolio Manager
- Track purchased domains
- View portfolio summary
- Monitor ROI performance
- Manage portfolio items (add/remove)
- Filter by status (holding, sold, monitoring)

### 📥 Export Features
- Export portfolio as CSV
- Export all analyzed domains
- Export top opportunities (score >= 70)
- Download data for analysis

### ⚙️ Settings
- Configure API base URL
- View system information
- Connection status monitoring

## Installation

### Option 1: Direct File (Recommended for MVP)
Simply open `index.html` in a web browser. No build process required!

```bash
# Navigate to frontend directory
cd frontend

# Open in browser (macOS)
open index.html

# Or with Python server
python3 -m http.server 8080
# Then visit http://localhost:8080
```

### Option 2: Web Server
Serve with any static web server:

```bash
# Using Python
python3 -m http.server 8080

# Using Node.js http-server
npx http-server

# Using PHP
php -S localhost:8080

# Using Python 2
python -m SimpleHTTPServer 8080
```

## API Connection

The dashboard connects to the FastAPI backend at `http://localhost:8000` by default.

To change the API URL:
1. Go to **Settings** tab
2. Update API Base URL
3. Click **Save Settings**

The URL is saved in browser localStorage, so you only need to set it once.

## Required Backend Endpoints

The dashboard expects these endpoints:

- `GET /api/health` - System health check
- `GET /api/domains/top-opportunities` - Top domains
- `GET /api/domains` - List all domains
- `GET /api/domains/{id}` - Domain details
- `POST /api/domains` - Add domain
- `GET /api/portfolio` - Portfolio summary and items
- `POST /api/portfolio` - Add to portfolio
- `PUT /api/portfolio/{id}` - Update item
- `DELETE /api/portfolio/{id}` - Remove from portfolio
- `GET /api/portfolio/export` - Export CSV
- `GET /api/domains/export` - Export all domains
- `GET /api/domains/export/top` - Export top opportunities

## UI Components

### Navigation Bar
- Application branding
- Quick access to all features

### Stat Boxes
- Animated stat display
- Real-time data updates
- Responsive grid layout

### Domain Cards
- Domain name and quality grade
- Detailed metrics (score, backlinks, age, value, ROI)
- Quick add-to-portfolio button
- Hover effects for better UX

### Portfolio Table
- Sortable columns
- Edit/delete capabilities
- Status badges
- ROI percentage display

### Export Panel
- One-click CSV downloads
- Multiple export formats
- Automatic file naming with date

## Design Details

### Color Scheme
- Primary: `#2196F3` (Blue)
- Success: `#4CAF50` (Green)
- Warning: `#FF9800` (Orange)
- Danger: `#f44336` (Red)

### Responsive Design
- Mobile-first approach
- Breakpoints at 768px
- Touch-friendly buttons
- Optimized for all screen sizes

### Accessibility
- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- High contrast colors

## Browser Support

- Chrome/Edge: Latest versions
- Firefox: Latest versions
- Safari: Latest versions
- Mobile browsers: Full support

## Performance

- Zero dependencies on build tools
- Lightweight JavaScript (~200 lines)
- Bootstrap CDN (cached globally)
- Font Awesome icons CDN
- Optimized CSS for fast rendering

## Troubleshooting

### "Unable to connect to API"
- Verify backend is running on correct port
- Check API URL in Settings
- Ensure CORS is enabled in FastAPI

### Data not updating
- Click "Refresh" button
- Check browser console for errors
- Verify API endpoints are working

### Export downloads not working
- Check browser download settings
- Try different export format
- Verify browser allows file downloads

## Development

To customize the dashboard:

1. Edit CSS in the `<style>` section
2. Modify HTML structure as needed
3. Update JavaScript in `<script>` section
4. No build process required - just refresh browser

## Deployment

### Vercel
```bash
vercel deploy ./frontend
```

### GitHub Pages
```bash
# Push frontend folder to gh-pages branch
git subtree push --prefix frontend origin gh-pages
```

### Docker
```dockerfile
FROM nginx:alpine
COPY frontend/ /usr/share/nginx/html/
```

### Simple HTTP Server
```bash
python3 -m http.server 8080 --directory frontend
```

## Future Enhancements

- Real-time notifications
- Advanced filtering and search
- Chart visualizations
- Domain comparison tool
- Alert management
- Domain recommendation engine
- Mobile native app
- Dark mode toggle
- Multi-user accounts

---

Built with ❤️ for domain investors
