import { useState } from "react";
import type { SiteTreeNode } from "../../api/inspector";

interface Props {
  nodes: SiteTreeNode[];
  selectedKey?: string | null;
  onSelect: (pageKey: string) => void;
}

function TreeItem({
  node,
  selectedKey,
  onSelect,
  depth,
}: {
  node: SiteTreeNode;
  selectedKey?: string | null;
  onSelect: (pageKey: string) => void;
  depth: number;
}) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children.length > 0;
  const isSelected = node.page_key === selectedKey;

  return (
    <li className="tree-item">
      <div className={`tree-row ${isSelected ? "selected" : ""}`}>
        {hasChildren ? (
          <button type="button" className="tree-toggle" onClick={() => setOpen(!open)}>
            {open ? "▾" : "▸"}
          </button>
        ) : (
          <span className="tree-toggle spacer" />
        )}
        <button
          type="button"
          className="tree-label"
          disabled={!node.page_key}
          onClick={() => node.page_key && onSelect(node.page_key)}
        >
          {node.label}
          {node.section && <span className="tree-badge">{node.section}</span>}
          {node.page_type && <span className="tree-type">{node.page_type}</span>}
        </button>
      </div>
      {hasChildren && open && (
        <ul className="tree-children">
          {node.children.map((child) => (
            <TreeItem
              key={child.path}
              node={child}
              selectedKey={selectedKey}
              onSelect={onSelect}
              depth={depth + 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function SiteTreeView({ nodes, selectedKey, onSelect }: Props) {
  if (nodes.length === 0) {
    return <p className="muted">درختی موجود نیست — Site Map را اجرا کنید.</p>;
  }
  return (
    <ul className="site-tree">
      {nodes.map((node) => (
        <TreeItem
          key={node.path}
          node={node}
          selectedKey={selectedKey}
          onSelect={onSelect}
          depth={0}
        />
      ))}
    </ul>
  );
}
