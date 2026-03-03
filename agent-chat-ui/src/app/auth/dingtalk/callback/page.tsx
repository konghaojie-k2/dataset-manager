"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function DingTalkCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
  const [message, setMessage] = useState("正在处理钉钉登录...")

  useEffect(() => {
    const code = searchParams.get("code")
    const state = searchParams.get("state")

    if (!code) {
      setStatus("error")
      setMessage("未收到授权码")
      setTimeout(() => router.push("/login"), 2000)
      return
    }

    handleCallback(code, state)
  }, [searchParams, router])

  const handleCallback = async (code: string, state: string | null) => {
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

      // 保存token和用户信息
      localStorage.setItem("access_token", data.access_token)
      localStorage.setItem("user", JSON.stringify(data.user))

      setStatus("success")
      setMessage("登录成功！正在跳转...")

      // 延迟跳转到首页
      setTimeout(() => {
        router.push("/")
      }, 1000)
    } catch (error) {
      console.error("钉钉登录失败:", error)
      setStatus("error")
      setMessage("登录失败，请重试")

      // 延迟跳转回登录页
      setTimeout(() => {
        router.push("/login")
      }, 2000)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">
            {status === "loading" && "处理中"}
            {status === "success" && "成功"}
            {status === "error" && "失败"}
          </CardTitle>
          <CardDescription>{message}</CardDescription>
        </CardHeader>
        <CardContent>
          {status === "loading" && (
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
            </div>
          )}
          {status === "success" && (
            <div className="text-center text-green-600">
              <svg
                className="w-16 h-16 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          )}
          {status === "error" && (
            <div className="text-center text-red-600">
              <svg
                className="w-16 h-16 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}