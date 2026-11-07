"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Spinner } from "@/components/Feedback";
import { useAuth } from "@/lib/auth";
import { roleHome } from "@/lib/format";

/** Sends each visitor to the area that matches the role reported by /api/auth/me/. */
export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (loading) return;
    router.replace(user ? roleHome(user.role) : "/login");
  }, [loading, user, router]);
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Spinner label="Loading CampusFix..." />
    </div>
  );
}