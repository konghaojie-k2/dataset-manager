import { useState, useCallback } from "react";
import { useStreamContext } from "@/providers/Stream";
import { Message } from "@langchain/langgraph-sdk";
import { A2UIFormDebug } from "@/components/a2ui/A2UIFormDebug";
import { chatAPI } from "@/lib/api-extension";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import type { A2UISchema, A2UIField } from "@/lib/api-extension";

interface A2UIFormData {
  schema: A2UISchema;
  clarification_reason: string;
  message: string;
}

interface A2UIFormMessageProps {
  message: Message;
  toolCallId: string;
  formData: A2UIFormData;
}

function sanitizeField(field: A2UIField): A2UIField {
  return {
    name: String(field.name || ""),
    type: ['text', 'select', 'multiselect', 'range', 'date_range', 'toggle'].includes(field.type) 
      ? field.type 
      : 'text',
    label: String(field.label || field.name || ""),
    placeholder: field.placeholder ? String(field.placeholder) : undefined,
    options: Array.isArray(field.options) 
      ? field.options.map(opt => ({
          value: String(opt.value || ""),
          label: String(opt.label || "")
        }))
      : undefined,
    required: Boolean(field.required),
    validation: field.validation && typeof field.validation === "object" 
      ? field.validation 
      : undefined,
    default: field.default
  };
}

function sanitizeSchema(schema: A2UISchema): A2UISchema {
  return {
    version: String(schema.version || "1.0"),
    form_id: String(schema.form_id || "default"),
    form_type: String(schema.form_type || "search_refinement"),
    title: String(schema.title || "请完善信息"),
    description: String(schema.description || ""),
    fields: Array.isArray(schema.fields) 
      ? schema.fields.map(sanitizeField) 
      : [],
    actions: Array.isArray(schema.actions) 
      ? schema.actions.map(action => ({
          id: String(action.id || "submit"),
          type: ['submit', 'button', 'cancel'].includes(action.type) ? action.type : 'submit',
          label: String(action.label || "提交"),
          primary: Boolean(action.primary)
        }))
      : []
  };
}

export function A2UIFormMessage({ message, toolCallId, formData }: A2UIFormMessageProps) {
  const { submit } = useStreamContext();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionId] = useState(() => `a2ui-${Date.now()}`);

  const safeSchema = sanitizeSchema(formData.schema);
  const safeMessage = typeof formData.message === "string" ? formData.message : "请完善以下信息";
  const safeReason = typeof formData.clarification_reason === "string" ? formData.clarification_reason : "";

  const handleSubmit = useCallback(async (data: Record<string, any>) => {
    if (!submit) return;

    setIsSubmitting(true);
    try {
      const formContent = JSON.stringify(data, null, 2);
      const formMessage: Message = {
        type: "human",
        content: formContent
      };

      submit(
        { messages: [formMessage] },
        {
          streamMode: ["values"],
          streamSubgraphs: true,
          streamResumable: true,
        },
      );
    } catch (error) {
      console.error("表单提交失败:", error);
    } finally {
      setIsSubmitting(false);
    }
  }, [submit]);

  return (
    <div className="mt-2">
      <Card className="w-full max-w-md border-[#c75b39]/30 bg-white shadow-md">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            {safeMessage}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isSubmitting ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="ml-2 text-sm text-muted-foreground">提交中...</span>
            </div>
          ) : (
            <A2UIFormDebug
              schema={safeSchema}
              sessionId={sessionId}
              onSubmit={handleSubmit}
              onCancel={() => {}}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export function findA2UIFormInMessages(messages: Message[]): Map<string, A2UIFormData> {
  const result = new Map<string, A2UIFormData>();

  const toolCallIdToResult = new Map<string, any>();

  messages.forEach((msg) => {
    if (msg.type === "tool" && msg.tool_call_id) {
      try {
        const content = msg.content;
        const parsed = typeof content === "string" ? JSON.parse(content) : content;
        toolCallIdToResult.set(msg.tool_call_id, parsed);
      } catch {
        toolCallIdToResult.set(msg.tool_call_id, msg.content);
      }
    }
  });

  messages.forEach((msg) => {
    if (msg.type === "ai" && msg.tool_calls) {
      for (const toolCall of msg.tool_calls) {
        if (toolCall.name === "clarify_intent") {
          const toolResult = toolCallIdToResult.get(toolCall.id);
          if (toolResult) {
            try {
              const parsed = typeof toolResult === "string" ? JSON.parse(toolResult) : toolResult;
              if (parsed.type === "ui_form" && parsed.form_schema) {
                result.set(toolCall.id, {
                  schema: parsed.form_schema,
                  clarification_reason: parsed.clarification_reason || "",
                  message: parsed.message || "请完善以下信息"
                });
              }
            } catch {
              // 不是 JSON，忽略
            }
          }
        }
      }
    }
  });

  return result;
}
