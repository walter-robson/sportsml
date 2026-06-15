import * as React from "react";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

type Props = {
  children: React.ReactNode;
};

export function WorkbenchShell({ children }: Props) {
  return (
    <div className="grid grid-cols-[200px_1fr] h-screen bg-bg overflow-hidden">
      <Sidebar />
      <div className="flex flex-col overflow-hidden">
        <Topbar activeRun={null} />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
