import * as React from "react";
import { cn } from "@/lib/utils";

export function Avatar({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-muted", className)} {...props} />;
}
