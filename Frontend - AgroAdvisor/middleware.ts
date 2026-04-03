import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Check if we are trying to access a protected route (anything under /dashboard)
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    
    // Look for our simple auth cookie
    const token = request.cookies.get('auth_token')
    
    if (!token) {
      // Setup the redirect URL keeping track of where they wanted to go (optional but nice)
      const loginUrl = new URL('/login', request.url)
      
      return NextResponse.redirect(loginUrl)
    }
  }

  // If trying to access login page while already authenticated, redirect to dashboard
  if (request.nextUrl.pathname === '/login') {
    const token = request.cookies.get('auth_token')
    if (token) {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
  }

  return NextResponse.next()
}

// Specify WHICH routes this middleware should run on.
// This improves performance by not running middleware on static assets.
export const config = {
  matcher: [
    '/dashboard',        // Exact match
    '/dashboard/:path*', // Protect all dashboard routes
    '/login'             // Catch authenticated users trying to access login
  ],
}
