import TopNav from "./TopNav";

export default function AppShell({ children, narrow = false }) {
  return (
    <>
      <TopNav />
      <div style={{ paddingTop: 96, paddingBottom: 96 }}>
        <div className="shell" style={narrow ? { maxWidth: 720 } : undefined}>
          {children}
        </div>
      </div>
    </>
  );
}
