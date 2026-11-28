import { Activity, LogOut, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { sair } from "@/app/login/actions";
import { Button } from "@/components/ui/button";
import { MonitorInatividade } from "@/components/monitor-inatividade";

export function Topbar() {
  return <><MonitorInatividade /><header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-5 sm:px-8"><Link href="/pacientes" className="alvo flex items-center gap-3" aria-label="Saúde 3D, página de pacientes"><span className="grid size-9 place-items-center rounded-md bg-teal-800 text-white"><Activity className="size-5" aria-hidden="true" /></span><span className="text-sm font-semibold text-slate-900">Saúde <span className="text-teal-800">3D</span></span></Link><div className="flex items-center gap-4"><span className="hidden items-center gap-1.5 text-xs text-slate-600 sm:flex"><ShieldCheck className="size-4 text-teal-700" aria-hidden="true" />Ambiente protegido</span><form action={sair}><Button type="submit" variant="ghost" className="h-9 px-2 sm:px-3"><LogOut className="size-4" aria-hidden="true" /><span className="sr-only sm:not-sr-only">Sair</span></Button></form></div></header></>;
}
