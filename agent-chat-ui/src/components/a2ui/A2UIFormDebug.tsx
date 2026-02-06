import { useState } from "react";
import { type A2UISchema } from "@/lib/api-extension";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface A2UIFormDebugProps {
  schema: A2UISchema;
  sessionId: string;
  onSubmit: (data: Record<string, any>) => void;
  onCancel?: () => void;
}

function isPrimitive(value: any): boolean {
  return value === null || (typeof value !== "object" && typeof value !== "function");
}

function isValidReactChild(value: any): boolean {
  return isPrimitive(value) || Array.isArray(value);
}

function toString(value: any): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) return JSON.stringify(value);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function A2UIFormDebug({ schema, sessionId, onSubmit, onCancel }: A2UIFormDebugProps) {
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initialData: Record<string, any> = {};
    if (Array.isArray(schema.fields)) {
      schema.fields.forEach((field) => {
        if (field.default !== undefined) {
          initialData[field.name] = field.default;
        }
      });
    }
    return initialData;
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      onSubmit(formData);
    } catch (error) {
      console.error("表单提交失败:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  console.log("[A2UIFormDebug] schema:", {
    title: schema.title,
    description: schema.description,
    fields: schema.fields?.map(f => ({ name: f.name, type: f.type }))
  });

  return (
    <div className="border rounded-lg p-4 bg-white w-full max-w-md">
      <h3 className="text-lg font-bold mb-2">
        {toString(schema.title)}
      </h3>
      {schema.description && (
        <p className="text-sm text-gray-500 mb-4">
          {toString(schema.description)}
        </p>
      )}

      <div className="space-y-4">
        {Array.isArray(schema.fields) && schema.fields.map((field) => (
          <div key={String(field.name)} className="space-y-2">
            <Label>
              {toString(field.label)}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </Label>

            {field.type === "text" && (
              <Input
                value={toString(formData[field.name] ?? "")}
                onChange={(e) => handleFieldChange(field.name, e.target.value)}
                placeholder={toString(field.placeholder)}
              />
            )}

            {field.type === "select" && Array.isArray(field.options) && (
              <select
                value={toString(formData[field.name] ?? "")}
                onChange={(e) => handleFieldChange(field.name, e.target.value)}
                className="flex h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm"
              >
                <option value="">{toString(field.placeholder) || "请选择"}</option>
                {field.options.map((opt) => (
                  <option key={String(opt.value)} value={String(opt.value)}>
                    {toString(opt.label)}
                  </option>
                ))}
              </select>
            )}

            {field.type === "multiselect" && Array.isArray(field.options) && (
              <div className="flex flex-wrap gap-2">
                {field.options.map((opt) => {
                  const currentValue = Array.isArray(formData[field.name]) ? formData[field.name] : [];
                  const isSelected = currentValue.includes(opt.value);
                  return (
                    <button
                      key={String(opt.value)}
                      type="button"
                      onClick={() => {
                        const current = Array.isArray(formData[field.name]) ? formData[field.name] : [];
                        if (isSelected) {
                          handleFieldChange(field.name, current.filter((v: string) => v !== opt.value));
                        } else {
                          handleFieldChange(field.name, [...current, opt.value]);
                        }
                      }}
                      className={cn(
                        "px-3 py-1 rounded-full text-sm border",
                        isSelected ? "bg-blue-500 text-white" : "bg-gray-100"
                      )}
                    >
                      {toString(opt.label)}
                    </button>
                  );
                })}
              </div>
            )}

            {field.type === "range" && (
              <div className="space-y-1">
                <input
                  type="range"
                  min={typeof field.validation?.min === "number" ? field.validation.min : 0}
                  max={typeof field.validation?.max === "number" ? field.validation.max : 100}
                  value={typeof formData[field.name] === "number" ? formData[field.name] : 0}
                  onChange={(e) => handleFieldChange(field.name, Number(e.target.value))}
                  className="w-full"
                />
                <p className="text-sm text-gray-500">
                  当前值: {toString(formData[field.name])}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-2 mt-4">
        {onCancel && (
          <Button variant="outline" onClick={onCancel}>
            取消
          </Button>
        )}
        <Button onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          提交
        </Button>
      </div>
    </div>
  );
}
