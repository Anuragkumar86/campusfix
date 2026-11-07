"use client";

import type { ReactNode } from "react";
import { adminLink } from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { useAuth } from "@/lib/auth";

const BASE = [
  { href: "/manager", label: "Dashboard" },
  { href: "/manager/tickets", label: "Ticket queue" },
  { href: "/manager/tickets?unassigned=true", label: "Unassigned" },
  { href: "/manager/overdue", label: "Overdue" },
  { href: "/manager/reports", label: "Reports" },
];

export default function ManagerLayout({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const nav = user?.role === "ADMINISTRATOR" ? [...BASE, adminLink] : BASE;
  return <RoleGuard roles={["DEPARTMENT_MANAGER", "ADMINISTRATOR"]} nav={nav}>{children}</RoleGuard>;
}
