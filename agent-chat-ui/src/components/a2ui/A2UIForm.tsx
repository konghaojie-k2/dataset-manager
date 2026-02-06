import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { A2UISchema, A2UIField, A2UIAction } from "@/lib/api-extension";
import { chatAPI } from "@/lib/api-extension";

interface A2UIFormProps {
  schema: A2UISchema;
  sessionId: string;
  onSubmit: (data: Record<string, any>) => void;
  onCancel?: () => void;
  className?: string;
}

export function A2UIForm({ schema, sessionId, onSubmit, onCancel, className }: A2UIFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initialData: Record<string, any> = {};
    schema.fields.forEach((field) => {
      if (field.default !== undefined) {
        initialData[field.name] = field.default;
      }
    });
    return initialData;
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    if (errors[fieldName]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    schema.fields.forEach((field) => {
      if (field.required && (formData[field.name] === undefined || formData[field.name] === "" || formData[field.name] === null)) {
        newErrors[field.name] = "此字段为必填项";
      }

      if (field.validation) {
        const validation = field.validation;
        if (validation.minLength && String(formData[field.name]).length < validation.minLength) {
          newErrors[field.name] = `最少需要 ${validation.minLength} 个字符`;
        }
        if (validation.maxLength && String(formData[field.name]).length > validation.maxLength) {
          newErrors[field.name] = `最多允许 ${validation.maxLength} 个字符`;
        }
        if (validation.pattern) {
          const regex = new RegExp(validation.pattern);
          if (!regex.test(formData[field.name])) {
            newErrors[field.name] = "格式不正确";
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (action?: A2UIAction) => {
    if (action?.type === "cancel" || action?.id === "cancel") {
      onCancel?.();
      return;
    }

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await chatAPI.submitForm(sessionId, schema.form_type, formData);
      onSubmit(response);
    } catch (error) {
      console.error("表单提交失败:", error);
      setErrors({ submit: "提交失败，请重试" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderField = (field: A2UIField) => {
    const fieldAny = field as any;
    const error = errors[field.name];
    const hasError = !!error;

    const safeLabel = typeof fieldAny.label === "string" ? fieldAny.label : String(fieldAny.name || "");
    const safePlaceholder = typeof fieldAny.placeholder === "string" ? fieldAny.placeholder : undefined;
    const safeOptions = Array.isArray(fieldAny.options) ? fieldAny.options : [];

    console.log("[A2UIForm] Rendering field:", {
      name: field.name,
      type: field.type,
      label: safeLabel,
      validation: field.validation
    });

    switch (field.type) {
      case "select":
        return (
          <div key={field.name} className="space-y-2">
            <Label htmlFor={field.name} className={cn(field.required && "after:content-['*'] after:text-destructive after:ml-1")}>
              {safeLabel}
            </Label>
            <select
              id={field.name}
              value={formData[field.name] ?? ""}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              className={cn(
                "flex h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow]",
                "border-input file:text-foreground file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium",
                "placeholder:text-muted-foreground",
                "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
                "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
                hasError && "border-destructive focus-visible:ring-destructive/20"
              )}
              required={field.required}
            >
              <option value="" disabled>
                {safePlaceholder || "请选择"}
              </option>
              {safeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {hasError && <p className="text-xs text-destructive">{error}</p>}
          </div>
        );

      case "multiselect":
        return (
          <div key={field.name} className="space-y-2">
            <Label htmlFor={field.name} className={cn(field.required && "after:content-['*'] after:text-destructive after:ml-1")}>
              {safeLabel}
            </Label>
            <div className="flex flex-wrap gap-2">
              {safeOptions.map((option) => {
                const currentValue = Array.isArray(formData[field.name]) ? formData[field.name] : [];
                const isSelected = currentValue.includes(option.value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      const current = Array.isArray(formData[field.name]) ? formData[field.name] : [];
                      if (isSelected) {
                        handleFieldChange(field.name, current.filter((v: string) => v !== option.value));
                      } else {
                        handleFieldChange(field.name, [...current, option.value]);
                      }
                    }}
                    className={cn(
                      "px-3 py-1 rounded-full text-sm border transition-colors",
                      isSelected
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background hover:bg-accent border-input"
                    )}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
            {hasError && <p className="text-xs text-destructive">{error}</p>}
          </div>
        );

      case "toggle":
        return (
          <div key={field.name} className="flex items-center justify-between">
            <Label htmlFor={field.name} className={cn(field.required && "after:content-['*'] after:text-destructive after:ml-1")}>
              {safeLabel}
            </Label>
            <button
              type="button"
              role="switch"
              aria-checked={formData[field.name] ?? false}
              onClick={() => handleFieldChange(field.name, !formData[field.name])}
              className={cn(
                "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent",
                "transition-colors duration-200 ease-in-out",
                "focus-visible:ring-ring/50 focus-visible:ring-[3px]",
                "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
                formData[field.name] ? "bg-primary" : "bg-input"
              )}
            >
              <span
                className={cn(
                  "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0",
                  "transition duration-200 ease-in-out",
                  formData[field.name] ? "translate-x-5" : "translate-x-0"
                )}
              />
            </button>
          </div>
        );

      case "range": {
        const validation = field.validation;
        const min = typeof validation?.min === "number" ? validation.min : 0;
        const max = typeof validation?.max === "number" ? validation.max : 100;
        return (
          <div key={field.name} className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor={field.name} className={cn(field.required && "after:content-['*'] after:text-destructive after:ml-1")}>
                {safeLabel}
              </Label>
              <span className="text-sm text-muted-foreground">
                {formData[field.name] ?? min} - {max}
              </span>
            </div>
            <input
              type="range"
              id={field.name}
              min={min}
              max={max}
              value={formData[field.name] ?? min}
              onChange={(e) => handleFieldChange(field.name, Number(e.target.value))}
              className="w-full"
            />
            {safePlaceholder && <p className="text-xs text-muted-foreground">{safePlaceholder}</p>}
          </div>
        );
      }

      case "text":
      default:
        return (
          <div key={field.name} className="space-y-2">
            <Label htmlFor={field.name} className={cn(field.required && "after:content-['*'] after:text-destructive after:ml-1")}>
              {safeLabel}
            </Label>
            <Input
              id={field.name}
              type="text"
              placeholder={safePlaceholder}
              value={formData[field.name] ?? ""}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              required={field.required}
              className={hasError ? "border-destructive focus-visible:ring-destructive/20" : ""}
            />
            {hasError && <p className="text-xs text-destructive">{error}</p>}
          </div>
        );
    }
  };

  const getPrimaryAction = (): A2UIAction | undefined => {
    return schema.actions.find((action) => action.primary) || schema.actions.find((action) => action.type === "submit");
  };

  const safeTitle = typeof schema.title === "string" ? schema.title : "请完善信息";
  const safeDescription = typeof schema.description === "string" ? schema.description : "";

  const safeActions = Array.isArray(schema.actions) ? schema.actions : [];

  return (
    <Card className={cn("w-full max-w-md", className)}>
      <CardHeader>
        <CardTitle>{safeTitle}</CardTitle>
        {safeDescription && <CardDescription>{safeDescription}</CardDescription>}
      </CardHeader>
      <CardContent>
        <form className="space-y-4">
          {schema.fields.map((field) => renderField(field))}
          {errors.submit && (
            <p className="text-sm text-destructive text-center">{errors.submit}</p>
          )}
        </form>
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        {safeActions
          .filter((action) => action.type === "cancel" || action.id === "cancel")
          .map((action) => (
            <Button
              key={String(action.id)}
              variant="outline"
              onClick={() => handleSubmit(action)}
              disabled={isSubmitting}
            >
              {String(action.label)}
            </Button>
          ))}
        {safeActions
          .filter((action) => action.type === "submit" || action.id === "submit" || action.primary)
          .map((action) => (
            <Button
              key={String(action.id)}
              variant={action.primary ? "default" : "default"}
              onClick={() => handleSubmit(action)}
              disabled={isSubmitting}
            >
              {isSubmitting ? "提交中..." : String(action.label)}
            </Button>
          ))}
      </CardFooter>
    </Card>
  );
}
