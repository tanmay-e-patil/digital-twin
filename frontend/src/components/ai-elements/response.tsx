import { cn } from "@/lib/utils";
import { type ComponentProps } from "react";

export function Response({ className, ...props }: ComponentProps<"p">) {
  return <p className={cn("whitespace-pre-wrap", className)} {...props} />;
}
