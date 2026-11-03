"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type HomeStatus =
  | { kind: "checking" }
  | { kind: "guest" }
  | { kind: "signed-in"; email: string }
  | { kind: "error"; message: string };

type CurrentUserResponse = {
  email: string;
};

async function getCurrentUser(): Promise<Response> {
  let response = await fetch(`${apiUrl}/auth/me`, { credentials: "include" });
  if (response.status === 401) {
    const refreshResponse = await fetch(`${apiUrl}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "X-Auth-Transport": "cookie" },
    });
    if (refreshResponse.ok) {
      response = await fetch(`${apiUrl}/auth/me`, { credentials: "include" });
    } else if (refreshResponse.status !== 401) {
      return refreshResponse;
    }
  }
  return response;
}

export default function HomePage() {
  const [status, setStatus] = useState<HomeStatus>({ kind: "checking" });

  useEffect(() => {
    let active = true;

    async function checkSession() {
      try {
        const response = await getCurrentUser();
        if (!active) {
          return;
        }
        if (response.status === 401) {
          setStatus({ kind: "guest" });
          return;
        }
        if (!response.ok) {
          setStatus({
            kind: "error",
            message: "La session n’a pas pu être vérifiée. Réessayez plus tard.",
          });
          return;
        }
        const user = (await response.json()) as CurrentUserResponse;
        setStatus({ kind: "signed-in", email: user.email });
      } catch {
        if (active) {
          setStatus({
            kind: "error",
            message: "Impossible de joindre le serveur pour vérifier la session.",
          });
        }
      }
    }

    void checkSession();
    return () => {
      active = false;
    };
  }, []);

  async function handleLogout() {
    try {
      const response = await fetch(`${apiUrl}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: { "X-Auth-Transport": "cookie" },
      });
      if (!response.ok) {
        setStatus({
          kind: "error",
          message: "La déconnexion n’a pas pu être confirmée par le serveur.",
        });
        return;
      }
      setStatus({ kind: "guest" });
    } catch {
      setStatus({
        kind: "error",
        message: "Impossible de joindre le serveur pour terminer la session.",
      });
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-12">
      <section className="w-full max-w-2xl rounded-2xl bg-white p-8 shadow-sm sm:p-12">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          Health V1
        </p>
        <h1 className="mt-3 text-4xl font-semibold text-zinc-900">
          Bienvenue sur Health V1
        </h1>
        <p className="mt-4 text-zinc-600">
          Votre espace pour prendre soin de votre santé.
        </p>

        {status.kind === "checking" && (
          <p className="mt-8 text-sm text-zinc-600" role="status">
            Vérification de votre session…
          </p>
        )}

        {status.kind === "guest" && (
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              className="rounded-lg bg-teal-700 px-5 py-3 text-center font-medium text-white hover:bg-teal-800"
              href="/subscribe"
            >
              Créer un compte
            </Link>
            <Link
              className="rounded-lg border border-zinc-300 px-5 py-3 text-center font-medium text-zinc-800 hover:bg-zinc-50"
              href="/login"
            >
              Se connecter
            </Link>
          </div>
        )}

        {status.kind === "signed-in" && (
          <div className="mt-8 space-y-4">
            <p className="rounded-lg bg-teal-50 p-4 text-teal-900" role="status">
              Vous êtes connecté en tant que {status.email}.
            </p>
            <button
              className="rounded-lg border border-zinc-300 px-5 py-3 font-medium text-zinc-800 hover:bg-zinc-50"
              onClick={handleLogout}
              type="button"
            >
              Se déconnecter
            </button>
          </div>
        )}

        {status.kind === "error" && (
          <p className="mt-8 text-sm text-red-700" role="alert">
            {status.message}
          </p>
        )}
      </section>
    </main>
  );
}
