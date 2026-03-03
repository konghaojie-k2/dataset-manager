"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isLoading, setIsLoading] = useState(false)
  const [authUrl, setAuthUrl] = useState("")
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })

  // 获取钉钉授权URL
  useEffect(() => {
    const fetchAuthUrl = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/v1/auth/dingtalk/url")
        if (!response.ok) {
          console.error("获取授权URL失败")
          return
        }
        const data = await response.json()
        setAuthUrl(data.auth_url)
      } catch (error) {
        console.error("获取授权URL失败:", error)
      }
    }
    fetchAuthUrl()
  }, [])

  // 检查URL中是否包含code（从钉钉回调）
  useEffect(() => {
    const code = searchParams.get("code")
    const state = searchParams.get("state")

    if (code) {
      handleDingTalkCallback(code, state)
    }
  }, [searchParams])

  // 处理钉钉回调
  const handleDingTalkCallback = async (code: string, state: string | null) => {
    setIsLoading(true)
    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/dingtalk/callback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code, state }),
      })

      if (!response.ok) {
        throw new Error("钉钉登录失败")
      }

      const data = await response.json()

      // 保存token
      localStorage.setItem("access_token", data.access_token)
      localStorage.setItem("user", JSON.stringify(data.user))

      // 跳转到首页
      router.push("/")
    } catch (error) {
      console.error("钉钉登录失败:", error)
      alert("钉钉登录失败，请重试")
    } finally {
      setIsLoading(false)
    }
  }

  // 钉钉登录
  const handleDingTalkLogin = () => {
    if (authUrl) {
      window.location.href = authUrl
    } else {
      alert("正在获取授权URL，请稍后重试")
    }
  }

  // 普通登录
  const handleNormalLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      // TODO: 实现普通登录逻辑
      alert("普通登录功能待实现")
    } catch (error) {
      console.error("登录失败:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">登录</CardTitle>
          <CardDescription>选择登录方式</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 钉钉登录 */}
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">第三方登录</div>
            <Button
              onClick={handleDingTalkLogin}
              disabled={isLoading || !authUrl}
              className="w-full bg-[#0089FF] hover:bg-[#0077E6]"
              size="lg"
            >
              {isLoading ? "登录中..." : "使用钉钉登录"}
            </Button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                或
              </span>
            </div>
          </div>

          {/* 普通登录表单 */}
          <form onSubmit={handleNormalLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </div>
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full"
              size="lg"
            >
              {isLoading ? "登录中..." : "登录"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}