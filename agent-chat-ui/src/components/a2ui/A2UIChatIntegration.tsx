import { useState } from "react";
import { A2UIForm, type A2UISchema } from "./A2UIForm";
import { chatAPI, type ChatResponse } from "@/lib/api-extension";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Loader2, Sparkles } from "lucide-react";

interface A2UIChatIntegrationProps {
  sessionId: string;
  onFormSubmit: (response: ChatResponse) => void;
  className?: string;
}

export function A2UIChatIntegration({ sessionId, onFormSubmit, className }: A2UIChatIntegrationProps) {
  const [clarificationResponse, setClarificationResponse] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string>("");

  const handleSendMessage = async (content: string) => {
    setIsLoading(true);
    setMessage(content);
    try {
      const response = await chatAPI.send(sessionId, content);
      if (response.type === "clarification_needed" && response.a2ui_form) {
        setClarificationResponse(response);
      } else {
        onFormSubmit(response);
      }
    } catch (error) {
      console.error("发送消息失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = async (response: ChatResponse) => {
    setClarificationResponse(null);
    onFormSubmit(response);
  };

  const handleFormCancel = () => {
    setClarificationResponse(null);
  };

  if (!clarificationResponse) {
    return (
      <div className={cn("space-y-4", className)}>
        <Button
          variant="outline"
          onClick={() => handleSendMessage("帮我找一些数据集")}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              搜索中...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              搜索数据集
            </>
          )}
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {message && (
        <Card className="bg-muted/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">您的查询</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{message}</p>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Sparkles className="h-4 w-4" />
        <span>请完善以下信息以帮助我们找到更准确的数据集</span>
      </div>

      <A2UIForm
        schema={clarificationResponse.a2ui_form!}
        sessionId={sessionId}
        onSubmit={handleFormSubmit}
        onCancel={handleFormCancel}
      />
    </div>
  );
}
