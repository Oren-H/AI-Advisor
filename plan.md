Plan saved to: ~/.claude/plans/sharded-growing-cosmos.md · /plan to edit
     AI Advisor Deployment & Enhancement Plan

     Overview

     Deploy the AI Advisor application to production with Railway (backend) and Vercel (frontend), integrate Supabase for persistent user data storage with full 
     authentication, and enhance the frontend UX.

     Goals

     1. Deploy backend to Railway with ChromaDB persistent storage
     2. Deploy frontend to Vercel
     3. Integrate Supabase for user authentication and data persistence
     4. Improve frontend UX with better components and features

     Architecture After Implementation

     ┌─────────────────────────────────────────────────────────┐
     │  Frontend (Vercel)                                      │
     │  - React + TypeScript + Vite                            │
     │  - Supabase Auth (login/signup)                         │
     │  - shadcn/ui components                                 │
     └─────────────────┬───────────────────────────────────────┘
                       │ HTTPS
                       ▼
     ┌─────────────────────────────────────────────────────────┐
     │  Backend (Railway)                                      │
     │  - FastAPI + LangGraph Agent                            │
     │  - ChromaDB (persistent volume)                         │
     │  - Supabase Client (user data)                          │
     └─────────────────┬───────────────────────────────────────┘
                       │
             ┌─────────┴──────────┐
             ▼                    ▼
     ┌───────────────┐    ┌──────────────────┐
     │   Supabase    │    │   ChromaDB       │
     │   PostgreSQL  │    │   Vector Store   │
     │               │    │   (Railway Vol)  │
     │  - users      │    │  - courses       │
     │  - profiles   │    │  - bulletin      │
     │  - convos     │    └──────────────────┘
     │  - messages   │
     └───────────────┘

     ---
     Phase 1: Backend Deployment Preparation

     1.1 Fix Dependency Management

     Issue: backend/requirements.txt and backend/pyproject.toml are empty

     Files to modify:
     - backend/requirements.txt (currently empty)

     Actions:
     - Scan all Python imports in backend/ directory
     - Generate comprehensive requirements.txt with pinned versions:
       - fastapi>=0.104.0
       - uvicorn[standard]>=0.24.0
       - langchain>=0.1.0
       - langgraph>=0.0.20
       - langchain-anthropic>=0.1.0
       - langchain-openai>=0.0.5
       - langchain-chroma>=0.1.0
       - chromadb>=0.4.0
       - pandas>=2.0.0
       - pypdf>=3.0.0
       - python-dotenv>=1.0.0
       - supabase>=2.0.0 (new)
       - pydantic>=2.0.0

     1.2 Create Railway Deployment Config

     New files to create:
     - backend/railway.json or railway.toml (Railway config)
     - backend/Procfile (process definition)
     - backend/.env.example (template for environment variables)

     railway.toml example:
     [build]
     builder = "NIXPACKS"
     buildCommand = "pip install -r requirements.txt"

     [deploy]
     startCommand = "python app/run_api.py"
     restartPolicyType = "ON_FAILURE"
     restartPolicyMaxRetries = 10

     [volumes]
       [volumes.databases]
         mountPath = "/app/databases/data"

     Environment variables to configure in Railway:
     - ANTHROPIC_API_KEY
     - OPENAI_API_KEY
     - LANGSMITH_API_KEY (optional)
     - SUPABASE_URL
     - SUPABASE_KEY
     - SUPABASE_SERVICE_ROLE_KEY
     - HOST=0.0.0.0
     - PORT=8000

     1.3 Update CORS Configuration

     File: backend/app/api.py (line ~30)

     Current (insecure):
     app.add_middleware(
         CORSMiddleware,
         allow_origins=["*"],
         ...
     )

     Update to:
     ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

     app.add_middleware(
         CORSMiddleware,
         allow_origins=ALLOWED_ORIGINS,
         ...
     )

     ---
     Phase 2: Supabase Setup

     2.1 Create Supabase Project

     Manual steps (in Supabase Dashboard):
     1. Create new project at https://supabase.com
     2. Choose region (closest to Railway deployment)
     3. Set strong database password
     4. Wait for provisioning
     5. Note down: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

     2.2 Database Schema Design

     New SQL migration file: backend/supabase/schema.sql

     -- Enable UUID extension
     CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

     -- Users table (managed by Supabase Auth)
     -- No need to create, handled by auth.users

     -- User profiles table
     CREATE TABLE public.user_profiles (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
       major TEXT,
       department TEXT,
       semester INTEGER CHECK (semester >= 1 AND semester <= 8),
       completed_courses TEXT[], -- Array of course codes
       career_goals TEXT,
       preferences JSONB DEFAULT '{}',
       created_at TIMESTAMPTZ DEFAULT NOW(),
       updated_at TIMESTAMPTZ DEFAULT NOW()
     );

     -- Conversations table
     CREATE TABLE public.conversations (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
       title TEXT,
       created_at TIMESTAMPTZ DEFAULT NOW(),
       updated_at TIMESTAMPTZ DEFAULT NOW()
     );

     -- Messages table
     CREATE TABLE public.messages (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE NOT NULL,
       role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
       content TEXT NOT NULL,
       created_at TIMESTAMPTZ DEFAULT NOW()
     );

     -- Indexes for performance
     CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
     CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);
     CREATE INDEX idx_messages_conversation_id ON public.messages(conversation_id);
     CREATE INDEX idx_messages_created_at ON public.messages(created_at);

     -- Row Level Security (RLS) policies
     ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
     ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
     ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

     -- Policies: Users can only access their own data
     CREATE POLICY "Users can view own profile" ON public.user_profiles
       FOR SELECT USING (auth.uid() = user_id);

     CREATE POLICY "Users can insert own profile" ON public.user_profiles
       FOR INSERT WITH CHECK (auth.uid() = user_id);

     CREATE POLICY "Users can update own profile" ON public.user_profiles
       FOR UPDATE USING (auth.uid() = user_id);

     CREATE POLICY "Users can view own conversations" ON public.conversations
       FOR ALL USING (auth.uid() = user_id);

     CREATE POLICY "Users can view own messages" ON public.messages
       FOR ALL USING (
         conversation_id IN (
           SELECT id FROM public.conversations WHERE user_id = auth.uid()
         )
       );

     -- Function to auto-update updated_at timestamp
     CREATE OR REPLACE FUNCTION update_updated_at_column()
     RETURNS TRIGGER AS $$
     BEGIN
       NEW.updated_at = NOW();
       RETURN NEW;
     END;
     $$ language 'plpgsql';

     CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

     CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON public.conversations
       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

     How to apply:
     - Run in Supabase SQL Editor
     - Or save as migration file for version control

     2.3 Backend Supabase Integration

     New file: backend/app/supabase_client.py

     from supabase import create_client, Client
     import os
     from typing import Optional

     class SupabaseClient:
         _instance: Optional[Client] = None

         @classmethod
         def get_client(cls) -> Client:
             if cls._instance is None:
                 supabase_url = os.getenv("SUPABASE_URL")
                 supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

                 if not supabase_url or not supabase_key:
                     raise ValueError("Supabase credentials not configured")

                 cls._instance = create_client(supabase_url, supabase_key)

             return cls._instance

     def get_supabase() -> Client:
         return SupabaseClient.get_client()

     2.4 Update Backend API to Use Supabase

     File: backend/app/api.py

     Critical changes:
     1. Replace in-memory conversations: Dict[str, Dict[str, Any]] = {} with Supabase queries
     2. Add authentication middleware to verify JWT tokens
     3. Update all endpoints to read/write from Supabase

     Key endpoints to refactor:
     - POST /profile/initialize → Create row in user_profiles and conversations
     - GET /conversations → Query from Supabase where user_id = auth.uid()
     - GET /conversations/{conversation_id} → Join conversations + messages
     - POST /chat/stream → Save messages to messages table
     - PUT /conversations/{conversation_id}/profile → Update user_profiles
     - DELETE /conversations/{conversation_id} → Cascade delete (handled by FK)

     New authentication dependency:
     from fastapi import Depends, HTTPException, Header
     from app.supabase_client import get_supabase

     async def get_current_user(authorization: str = Header(None)):
         if not authorization:
             raise HTTPException(status_code=401, detail="Missing authorization header")

         try:
             token = authorization.replace("Bearer ", "")
             supabase = get_supabase()
             user = supabase.auth.get_user(token)
             return user
         except Exception as e:
             raise HTTPException(status_code=401, detail="Invalid token")

     Apply to protected endpoints:
     @app.get("/conversations")
     async def get_conversations(user = Depends(get_current_user)):
         supabase = get_supabase()
         result = supabase.table("conversations").select("*").eq("user_id", user.id).execute()
         return result.data

     ---
     Phase 3: Frontend Deployment Preparation

     3.1 Install Frontend Dependencies

     File: frontend/package.json

     Add dependencies:
     npm install @supabase/supabase-js
     npm install @tanstack/react-query
     npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select
     npm install class-variance-authority clsx tailwind-merge
     npm install lucide-react (already installed)

     3.2 Configure Supabase Client (Frontend)

     New file: frontend/src/lib/supabase.ts

     import { createClient } from '@supabase/supabase-js'

     const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
     const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

     if (!supabaseUrl || !supabaseAnonKey) {
       throw new Error('Missing Supabase environment variables')
     }

     export const supabase = createClient(supabaseUrl, supabaseAnonKey)

     // Type definitions
     export type UserProfile = {
       id: string
       user_id: string
       major: string | null
       department: string | null
       semester: number | null
       completed_courses: string[]
       career_goals: string | null
       preferences: Record<string, any>
       created_at: string
       updated_at: string
     }

     export type Conversation = {
       id: string
       user_id: string
       title: string | null
       created_at: string
       updated_at: string
     }

     export type Message = {
       id: string
       conversation_id: string
       role: 'user' | 'assistant'
       content: string
       created_at: string
     }

     3.3 Add Authentication Components

     New files to create:
     - frontend/src/components/AuthProvider.tsx - Context provider for auth state
     - frontend/src/components/LoginForm.tsx - Email/password login
     - frontend/src/components/SignUpForm.tsx - Registration form
     - frontend/src/components/ProtectedRoute.tsx - Route guard

     Example: frontend/src/components/AuthProvider.tsx
     import { createContext, useContext, useEffect, useState } from 'react'
     import { supabase } from '../lib/supabase'
     import { User, Session } from '@supabase/supabase-js'

     type AuthContextType = {
       user: User | null
       session: Session | null
       loading: boolean
       signIn: (email: string, password: string) => Promise<void>
       signUp: (email: string, password: string) => Promise<void>
       signOut: () => Promise<void>
     }

     const AuthContext = createContext<AuthContextType | undefined>(undefined)

     export function AuthProvider({ children }: { children: React.ReactNode }) {
       const [user, setUser] = useState<User | null>(null)
       const [session, setSession] = useState<Session | null>(null)
       const [loading, setLoading] = useState(true)

       useEffect(() => {
         supabase.auth.getSession().then(({ data: { session } }) => {
           setSession(session)
           setUser(session?.user ?? null)
           setLoading(false)
         })

         const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
           setSession(session)
           setUser(session?.user ?? null)
         })

         return () => subscription.unsubscribe()
       }, [])

       const signIn = async (email: string, password: string) => {
         const { error } = await supabase.auth.signInWithPassword({ email, password })
         if (error) throw error
       }

       const signUp = async (email: string, password: string) => {
         const { error } = await supabase.auth.signUp({ email, password })
         if (error) throw error
       }

       const signOut = async () => {
         const { error } = await supabase.auth.signOut()
         if (error) throw error
       }

       return (
         <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signOut }}>
           {children}
         </AuthContext.Provider>
       )
     }

     export const useAuth = () => {
       const context = useContext(AuthContext)
       if (!context) throw new Error('useAuth must be used within AuthProvider')
       return context
     }

     3.4 Update API Client to Include Auth Token

     File: frontend/src/api/chat.ts

     Modify fetch calls:
     import { supabase } from '../lib/supabase'

     async function getAuthHeader() {
       const { data: { session } } = await supabase.auth.getSession()
       return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}
     }

     export async function sendMessage(conversationId: string, message: string) {
       const authHeader = await getAuthHeader()

       const response = await fetch(`${API_URL}/chat`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
           ...authHeader,
         },
         body: JSON.stringify({ conversation_id: conversationId, message }),
       })

       if (!response.ok) throw new Error('Failed to send message')
       return response.json()
     }

     // Apply to all API functions...

     3.5 Update App.tsx for Authentication Flow

     File: frontend/src/components/App.tsx

     Changes:
     1. Wrap app in <AuthProvider>
     2. Show login/signup forms if not authenticated
     3. Show main chat UI if authenticated
     4. Add logout button

     3.6 Create Vercel Configuration

     New file: frontend/vercel.json

     {
       "buildCommand": "npm run build",
       "outputDirectory": "dist",
       "framework": "vite",
       "env": {
         "VITE_API_URL": "@api-url",
         "VITE_SUPABASE_URL": "@supabase-url",
         "VITE_SUPABASE_ANON_KEY": "@supabase-anon-key"
       }
     }

     Environment variables to set in Vercel dashboard:
     - VITE_API_URL=https://your-backend.railway.app
     - VITE_SUPABASE_URL=https://xxxxx.supabase.co
     - VITE_SUPABASE_ANON_KEY=eyJhb...

     ---
     Phase 4: Frontend UX Improvements

     4.1 Install shadcn/ui Component Library

     Commands:
     cd frontend
     npx shadcn@latest init
     npx shadcn@latest add button
     npx shadcn@latest add card
     npx shadcn@latest add input
     npx shadcn@latest add textarea
     npx shadcn@latest add dialog
     npx shadcn@latest add dropdown-menu
     npx shadcn@latest add select
     npx shadcn@latest add toast
     npx shadcn@latest add avatar
     npx shadcn@latest add badge
     npx shadcn@latest add separator

     4.2 Enhance Chat UX

     File: frontend/src/components/ChatBubble.tsx

     Add features:
     - Copy button (using lucide-react Copy icon)
     - Regenerate button for last assistant message
     - Timestamp display
     - Message reactions (thumbs up/down for feedback)

     File: frontend/src/components/StreamingText.tsx

     Add:
     - Typing indicator animation while streaming
     - Cursor blink effect

     4.3 Improve Profile Form

     File: frontend/src/components/ProfileForm.tsx

     Enhancements:
     - Multi-select dropdown for completed courses (use shadcn/ui Select with search)
     - Semester progress bar (visual indicator: 1/8, 2/8, etc.)
     - Department autocomplete
     - Major autocomplete from known majors list
     - Save indicators ("Saving...", "Saved!")

     4.4 Add Conversation Management UI

     New file: frontend/src/components/ConversationList.tsx

     Features:
     - List all conversations in sidebar
     - Rename conversation (double-click to edit)
     - Delete conversation (with confirmation dialog)
     - Create new conversation button
     - Active conversation highlight

     4.5 Add React Query for State Management

     New file: frontend/src/lib/queries.ts

     import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
     import * as api from '../api/chat'

     export function useConversations() {
       return useQuery({
         queryKey: ['conversations'],
         queryFn: api.getConversations,
       })
     }

     export function useConversation(conversationId: string) {
       return useQuery({
         queryKey: ['conversation', conversationId],
         queryFn: () => api.getConversation(conversationId),
         enabled: !!conversationId,
       })
     }

     export function useSendMessage() {
       const queryClient = useQueryClient()

       return useMutation({
         mutationFn: ({ conversationId, message }: { conversationId: string; message: string }) =>
           api.sendMessage(conversationId, message),
         onSuccess: (_, variables) => {
           queryClient.invalidateQueries({ queryKey: ['conversation', variables.conversationId] })
         },
       })
     }

     Update: frontend/src/main.tsx
     import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

     const queryClient = new QueryClient()

     ReactDOM.createRoot(document.getElementById('root')!).render(
       <React.StrictMode>
         <QueryClientProvider client={queryClient}>
           <AuthProvider>
             <App />
           </AuthProvider>
         </QueryClientProvider>
       </React.StrictMode>,
     )

     4.6 Add Accessibility Features

     Updates across components:
     - ARIA labels for all interactive elements
     - Keyboard shortcuts:
       - Cmd/Ctrl + K → Focus search/input
       - Cmd/Ctrl + N → New conversation
       - Esc → Close dialogs
     - Focus management (trap focus in modals)
     - Screen reader announcements for streaming messages

     4.7 Performance Optimizations

     File: frontend/src/components/MessageList.tsx

     Add:
     - Virtual scrolling for long conversations (use react-window or @tanstack/react-virtual)
     - Lazy loading for old messages
     - Debounce user input in search fields

     ---
     Phase 5: Deployment Steps

     5.1 Deploy Backend to Railway

     Steps:
     1. Install Railway CLI: npm i -g @railway/cli
     2. Login: railway login
     3. Initialize: railway init (in backend/ directory)
     4. Link to project: railway link
     5. Add volume for ChromaDB:
       - Go to Railway dashboard → Service → Variables
       - Add volume mount: /app/databases/data
     6. Set environment variables in Railway dashboard (see Phase 1.2)
     7. Deploy: railway up
     8. Note the deployed URL: https://your-backend.up.railway.app

     Verification:
     - Visit https://your-backend.up.railway.app/ (should return health check)
     - Check logs: railway logs

     5.2 Deploy Frontend to Vercel

     Steps:
     1. Install Vercel CLI: npm i -g vercel
     2. Login: vercel login
     3. Deploy from frontend/ directory: vercel --prod
     4. Set environment variables in Vercel dashboard:
       - VITE_API_URL → Railway backend URL
       - VITE_SUPABASE_URL → Supabase project URL
       - VITE_SUPABASE_ANON_KEY → Supabase anon key
     5. Redeploy: vercel --prod

     OR use GitHub integration:
     1. Push code to GitHub
     2. Import repository in Vercel dashboard
     3. Set root directory to frontend/
     4. Set environment variables
     5. Deploy

     Verification:
     - Visit deployed URL
     - Test login/signup
     - Send a message
     - Check conversation persistence

     5.3 Configure Production CORS

     In Railway environment variables:
     - Add: ALLOWED_ORIGINS=https://your-frontend.vercel.app

     Test:
     - Frontend should be able to call backend without CORS errors

     ---
     Phase 6: Testing & Validation

     6.1 Manual Testing Checklist

     - User can sign up with email/password
     - User can log in
     - User can create profile (major, semester, courses)
     - User can start new conversation
     - User can send message and receive streaming response
     - Agent can search courses via vector DB
     - Agent can look up major requirements
     - Conversation persists after page refresh
     - User can view past conversations
     - User can delete conversations
     - User can log out
     - Dark mode works
     - Mobile responsive design works

     6.2 Performance Testing

     - Backend responds within 2s for simple queries
     - Streaming starts within 500ms
     - ChromaDB queries complete within 1s
     - Frontend loads within 2s (First Contentful Paint)

     6.3 Security Validation

     - RLS policies prevent unauthorized data access
     - API endpoints require authentication
     - CORS restricted to frontend domain
     - No API keys exposed in frontend
     - Passwords hashed by Supabase Auth

     ---
     Critical Files to Modify

     Backend

     1. backend/requirements.txt - Add all dependencies
     2. backend/app/api.py - Replace in-memory storage with Supabase, add auth middleware
     3. backend/app/supabase_client.py - NEW: Supabase client singleton
     4. backend/railway.toml - NEW: Railway deployment config
     5. backend/.env.example - NEW: Template for environment variables

     Frontend

     6. frontend/src/lib/supabase.ts - NEW: Supabase client
     7. frontend/src/components/AuthProvider.tsx - NEW: Auth context
     8. frontend/src/components/LoginForm.tsx - NEW: Login UI
     9. frontend/src/components/SignUpForm.tsx - NEW: Signup UI
     10. frontend/src/components/App.tsx - Update to include auth flow
     11. frontend/src/api/chat.ts - Add auth headers to API calls
     12. frontend/src/main.tsx - Wrap in AuthProvider and QueryClientProvider
     13. frontend/vercel.json - NEW: Vercel deployment config
     14. frontend/package.json - Add new dependencies

     Database

     15. supabase/schema.sql - NEW: Database schema (run in Supabase SQL editor)

     ---
     Estimated Implementation Order

     Priority 1 (Core Functionality)

     1. Fix backend dependencies (requirements.txt)
     2. Set up Supabase project and run schema
     3. Create backend/app/supabase_client.py
     4. Update backend/app/api.py for Supabase integration
     5. Deploy backend to Railway
     6. Add Supabase client to frontend (frontend/src/lib/supabase.ts)
     7. Create authentication components (AuthProvider, LoginForm, SignUpForm)
     8. Update frontend API client with auth headers
     9. Deploy frontend to Vercel
     10. Test end-to-end flow

     Priority 2 (UX Improvements)

     11. Install shadcn/ui components
     12. Enhance ChatBubble with copy/regenerate buttons
     13. Improve ProfileForm with multi-select and autocomplete
     14. Add ConversationList sidebar
     15. Add React Query for state management

     Priority 3 (Polish)

     16. Add keyboard shortcuts
     17. Add accessibility features (ARIA labels)
     18. Performance optimizations (virtual scrolling, lazy loading)
     19. Add loading states and error handling
     20. Add user feedback mechanisms (toasts, confirmations)

     ---
     Environment Variables Reference

     Backend (.env)

     ANTHROPIC_API_KEY=sk-ant-...
     OPENAI_API_KEY=sk-proj-...
     LANGSMITH_API_KEY=lsv2_pt_... (optional)
     LANGSMITH_TRACING=true (optional)
     SUPABASE_URL=https://xxxxx.supabase.co
     SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
     ALLOWED_ORIGINS=https://your-frontend.vercel.app
     HOST=0.0.0.0
     PORT=8000

     Frontend (.env)

     VITE_API_URL=https://your-backend.railway.app
     VITE_SUPABASE_URL=https://xxxxx.supabase.co
     VITE_SUPABASE_ANON_KEY=eyJhbGc...

     ---
     Success Criteria

     - ✓ Backend deployed to Railway with persistent ChromaDB storage
     - ✓ Frontend deployed to Vercel
     - ✓ Users can sign up, log in, and manage their profiles
     - ✓ Conversations and messages persist in Supabase
     - ✓ Agent can search courses and provide academic advice
     - ✓ Frontend has improved UX with shadcn/ui components
     - ✓ Application is secure with RLS and authentication
     - ✓ Application is performant and responsive

     ---
     Rollback Plan

     If issues arise during deployment:
     1. Backend: Revert to last working Railway deployment
     2. Frontend: Revert Vercel deployment or roll back Git commit
     3. Supabase: Database snapshots taken before schema changes
     4. ChromaDB: Persistent volume ensures no data loss

     ---
     Future Enhancements (Post-MVP)

     - Email verification for sign-ups
     - Password reset flow
     - OAuth providers (Google, GitHub)
     - Real-time collaboration (multiple users in same conversation)
     - Export conversation as PDF
     - Course recommendations based on ML
     - Integration with Columbia's official course API
     - Mobile app (React Native)