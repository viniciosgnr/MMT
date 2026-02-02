
'use client'

import { useState } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { createClient } from '@/utils/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const supabase = createClient()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSignUp, setIsSignUp] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      if (isSignUp) {
        // Sign Up Logic
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        })
        if (error) {
          toast.error('Sign Up Failed', { description: error.message })
        } else {
          toast.success('Sign Up Successful', { description: 'Please check your email to confirm your account.' })
          setIsSignUp(false)
        }
      } else {
        // Login Logic
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (error) {
          toast.error('Login Failed', { description: error.message })
        } else {
          toast.success('Login Successful')
          router.push('/dashboard')
          router.refresh()
        }
      }
    } catch (err) {
      toast.error('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50 dark:bg-slate-900">
      {/* Left side - FPSO Image */}
      <div className="hidden lg:flex w-[60%] relative bg-slate-900">
        <Image
          src="/fpso-background.jpg"
          alt="FPSO Offshore"
          fill
          className="object-cover opacity-80"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/30 to-transparent" />

        <div className="absolute bottom-12 left-12 text-white p-4">
          <h2 className="text-4xl font-bold tracking-tight mb-2">Metrology Management Tool</h2>
          <p className="text-slate-200 text-lg opacity-90 max-w-md">
            Advanced management for offshore metering systems.
          </p>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        <Card className="w-full max-w-md border-none shadow-xl bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm">
          <CardHeader className="space-y-4 flex flex-col items-center text-center pb-2">
            <div className="relative w-48 h-20 mb-2">
              <Image
                src="/sbm-logo.png"
                alt="SBM Offshore"
                fill
                className="object-contain dark:brightness-0 dark:invert"
                priority
              />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-2xl font-bold tracking-tight">
                {isSignUp ? 'Create an Account' : 'Welcome Back'}
              </CardTitle>
              <CardDescription>
                {isSignUp ? 'Enter your details to register' : 'Sign in to your account'}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@sbmoffshore.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-white dark:bg-slate-900"
                  required
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  {!isSignUp && (
                    <a href="#" className="text-xs text-blue-600 hover:text-blue-500 dark:text-blue-400">
                      Forgot password?
                    </a>
                  )}
                </div>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-white dark:bg-slate-900"
                  required
                  minLength={6}
                />
              </div>
              <Button type="submit" className="w-full bg-orange-600 hover:bg-orange-700 text-white" disabled={isLoading}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSignUp ? 'Sign Up' : 'Sign In'}
              </Button>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col gap-4 pt-2">
            <div className="relative w-full">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-slate-200 dark:border-slate-800" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-transparent px-2 text-slate-500">
                  Or
                </span>
              </div>
            </div>
            <Button
              variant="outline"
              className="w-full border-slate-200 dark:border-slate-800"
              onClick={() => setIsSignUp(!isSignUp)}
              disabled={isLoading}
            >
              {isSignUp ? 'Already have an account? Sign In' : 'Create an account'}
            </Button>
            <p className="text-center text-xs text-slate-500 mt-2">
              By clicking continue, you agree to our Terms of Service and Privacy Policy.
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
