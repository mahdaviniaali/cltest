interface Props {
  href: string | null | undefined;
  children?: React.ReactNode;
  className?: string;
  title?: string;
}

export default function ExternalLink({ href, children, className, title }: Props) {
  const url = href?.trim();
  if (!url?.startsWith("http")) {
    return <span className={className}>{children ?? url ?? "—"}</span>;
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={className ?? "external-link"}
      title={title}
    >
      {children ?? url}
    </a>
  );
}
