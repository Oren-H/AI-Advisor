# AI Advisor Frontend

A lightweight, production-ready chat UI for the AI Advisor course recommendation system. Built with React + TypeScript, Vite, and TailwindCSS.

## Features

- 🎨 **ChatGPT-like Interface**: Clean, modern chat UI with responsive design
- 🌙 **Dark Mode**: Toggle between light and dark themes
- 📱 **Responsive**: Works on desktop and mobile devices
- ⚡ **Streaming**: Real-time token streaming from the backend
- 💾 **Local Storage**: Chat history persists across browser sessions
- ⌨️ **Keyboard Shortcuts**: ⌘/Ctrl+Enter to send messages
- ♿ **Accessible**: Full keyboard navigation and screen reader support
- 📝 **Markdown Support**: Rich text rendering for assistant responses

## Prerequisites

- Node.js 18+ and npm/pnpm
- Backend API running (see main project README)

## Installation

1. **Install dependencies:**
   ```bash
   pnpm install
   ```

2. **Set up environment variables:**
   Create a `.env` file in the frontend directory:
   ```bash
   VITE_API_URL=http://localhost:8000
   ```
   
   Replace with your actual backend URL if different.

3. **Start the development server:**
   ```bash
   pnpm dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm preview` - Preview production build
- `pnpm lint` - Run ESLint

## Project Structure

```
src/
├── components/          # React components
│   ├── App.tsx         # Main application component
│   ├── ChatBubble.tsx  # Individual message component
│   ├── InputBar.tsx    # Message input component
│   └── MessageList.tsx # Message list container
├── hooks/              # Custom React hooks
│   └── useChat.ts      # Chat state management
├── api/                # API utilities
│   └── chat.ts         # Chat API functions
├── types.ts            # TypeScript type definitions
└── main.tsx           # Application entry point
```

## Configuration

### Backend URL
Update the `VITE_API_URL` environment variable to point to your backend API. The default is `http://localhost:8000`.

### Styling
The app uses TailwindCSS with a custom configuration in `tailwind.config.js`. Key customizations:
- Inter font family
- Dark mode support (`darkMode: 'class'`)
- Custom animations for typing indicators

### Local Storage Keys
- `ai-advisor-chat-history`: Stores chat messages
- `ai-advisor-dark-mode`: Stores dark mode preference

## API Integration

The frontend expects a backend API with the following endpoint:

**POST** `/api/chat`
- **Body**: `{ "message": "string" }`
- **Response**: Server-Sent Events (SSE) stream with JSON data
- **Format**: `data: {"token": "string"}`

Example backend response:
```
data: {"token": "Hello"}
data: {"token": " "}
data: {"token": "there"}
data: [DONE]
```

## Development

### Adding New Features
1. Create components in `src/components/`
2. Add custom hooks in `src/hooks/`
3. Update types in `src/types.ts`
4. Add API functions in `src/api/`

### Styling Guidelines
- Use TailwindCSS utility classes
- Follow the existing color scheme (gray/indigo)
- Ensure dark mode compatibility
- Maintain accessibility standards

### Code Quality
- Use TypeScript for all new code
- Follow ESLint rules
- Add JSDoc comments for complex functions
- Test keyboard navigation and screen readers

## Troubleshooting

### Common Issues

**"Module not found" errors:**
- Run `pnpm install` to ensure all dependencies are installed
- Check that Node.js version is 18+

**Backend connection issues:**
- Verify `VITE_API_URL` is correct
- Ensure backend server is running
- Check CORS configuration on backend

**Dark mode not working:**
- Clear browser cache
- Check localStorage for corrupted data

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test on both light and dark themes
4. Ensure mobile responsiveness
5. Update documentation as needed 