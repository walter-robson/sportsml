"use client";

import * as React from "react";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import type { JsonSchema, JsonSchemaField } from "@/lib/types";
import { cn } from "@/lib/utils";

type FormValues = Record<string, unknown>;

type Props = {
  schema: JsonSchema;
  initialValues?: FormValues;
  onSubmit: (values: FormValues) => void;
  submitting: boolean;
  submitLabel?: string;
  hint?: string;
};

function defaultValuesFromSchema(schema: JsonSchema): FormValues {
  const out: FormValues = {};
  for (const [key, field] of Object.entries(schema.properties)) {
    if (field.default !== undefined) {
      out[key] = field.default;
    } else if (field.type === "boolean") {
      out[key] = false;
    } else if (field.type === "array") {
      out[key] = [];
    } else if (field.type === "integer" || field.type === "number") {
      out[key] = field.minimum ?? 0;
    } else {
      out[key] = "";
    }
  }
  return out;
}

function formatDisplay(value: unknown, field: JsonSchemaField): string {
  if (typeof value === "number") {
    if (field.type === "integer") return value.toString();
    // Show 2 decimals for fractional floats, 0 for integer-like.
    const step = field.multipleOf ?? 0.01;
    const decimals = step >= 1 ? 0 : step >= 0.1 ? 1 : 2;
    return value.toFixed(decimals);
  }
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "on" : "off";
  return String(value ?? "");
}

export function ModelConfigForm({
  schema,
  initialValues,
  onSubmit,
  submitting,
  submitLabel = "Run Model",
  hint,
}: Props) {
  const [values, setValues] = React.useState<FormValues>(() => ({
    ...defaultValuesFromSchema(schema),
    ...(initialValues ?? {}),
  }));

  const setField = React.useCallback((key: string, next: unknown) => {
    setValues((prev) => ({ ...prev, [key]: next }));
  }, []);

  const fields = Object.entries(schema.properties);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(values);
      }}
      className="flex flex-col gap-3"
    >
      {fields.map(([key, field]) => (
        <FieldRow
          key={key}
          fieldKey={key}
          field={field}
          value={values[key]}
          onChange={(next) => setField(key, next)}
        />
      ))}
      <Button type="submit" disabled={submitting} className="w-full mt-2">
        {submitting ? "Running…" : submitLabel}
      </Button>
      {hint && <div className="text-[10px] text-fg-fainter text-center italic mt-1">{hint}</div>}
    </form>
  );
}

type FieldRowProps = {
  fieldKey: string;
  field: JsonSchemaField;
  value: unknown;
  onChange: (next: unknown) => void;
};

function FieldRow({ fieldKey, field, value, onChange }: FieldRowProps) {
  if (field.type === "integer" || field.type === "number") {
    const min = field.minimum ?? 0;
    const max = field.maximum ?? 100;
    const step = field.multipleOf ?? (field.type === "integer" ? 1 : 0.05);
    const current = typeof value === "number" ? value : min;
    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex justify-between items-baseline mono text-[11px]">
          <span className="text-fg-muted">{fieldKey}</span>
          <span className="text-accent-blue">{formatDisplay(current, field)}</span>
        </div>
        <Slider
          min={min}
          max={max}
          step={step}
          value={[current]}
          onValueChange={(v) => onChange(v[0])}
        />
        {field.description && (
          <div className="text-[10px] text-fg-fainter italic">{field.description}</div>
        )}
      </div>
    );
  }

  if (field.type === "boolean") {
    const checked = Boolean(value);
    return (
      <div className="flex items-center justify-between gap-2 pt-1">
        <span className="mono text-[11px] text-fg-muted">{fieldKey}</span>
        <Switch checked={checked} onCheckedChange={onChange} />
      </div>
    );
  }

  if (field.type === "array" && field.items?.enum) {
    const arr = Array.isArray(value) ? (value as ReadonlyArray<string | number>) : [];
    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex justify-between items-baseline mono text-[11px]">
          <span className="text-fg-muted">{fieldKey}</span>
          <span className="text-accent-blue text-[10px]">
            {arr.length === 0 ? "none" : `${arr.length} selected`}
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {field.items.enum.map((opt) => {
            const optStr = String(opt);
            const on = arr.map(String).includes(optStr);
            return (
              <button
                key={optStr}
                type="button"
                onClick={() =>
                  onChange(on ? arr.filter((v) => String(v) !== optStr) : [...arr, opt])
                }
                className={cn(
                  "mono text-[10px] px-2 py-1 rounded border transition-colors",
                  on
                    ? "bg-[#22303a] border-[#27384a] text-accent-blue"
                    : "bg-bg-active border-border-strong text-fg-faint hover:text-fg",
                )}
              >
                {optStr}
              </button>
            );
          })}
        </div>
        {field.description && (
          <div className="text-[10px] text-fg-fainter italic">{field.description}</div>
        )}
      </div>
    );
  }

  return null;
}
