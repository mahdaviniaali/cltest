import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { SiteMap, SiteMapGroupNode } from "../../api/inspector";

interface Props {
  siteMap: SiteMap | null;
  selectedKey?: string | null;
  onSelect: (pageKey: string) => void;
}

const NODE_WIDTH = 200;
const NODE_HEIGHT = 72;
const GAP_X = 32;
const GAP_Y = 110;

function layoutTree(nodes: SiteMapGroupNode[]): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  const byKey = new Map(nodes.map((n) => [n.group_key, n]));
  const children = new Map<string, SiteMapGroupNode[]>();
  for (const node of nodes) {
    if (!node.parent_group_key) continue;
    const list = children.get(node.parent_group_key) ?? [];
    list.push(node);
    children.set(node.parent_group_key, list);
  }
  for (const list of children.values()) {
    list.sort((a, b) => b.weight - a.weight || b.page_count - a.page_count);
  }

  const roots = nodes.filter((n) => !n.parent_group_key || !byKey.has(n.parent_group_key));

  function layoutSubtree(key: string, depth: number, xStart: number): number {
    const kids = children.get(key) ?? [];
    if (kids.length === 0) {
      positions.set(key, { x: xStart, y: depth * GAP_Y });
      return xStart + NODE_WIDTH + GAP_X;
    }
    let cursor = xStart;
    for (const kid of kids) {
      cursor = layoutSubtree(kid.group_key, depth + 1, cursor);
    }
    const first = positions.get(kids[0].group_key)!;
    const last = positions.get(kids[kids.length - 1].group_key)!;
    positions.set(key, { x: (first.x + last.x) / 2, y: depth * GAP_Y });
    return cursor;
  }

  let x = 0;
  for (const root of roots) {
    x = layoutSubtree(root.group_key, 0, x);
    x += GAP_X;
  }
  return positions;
}

function kindLabel(kind: string): string {
  switch (kind) {
    case "root":
      return "ریشه";
    case "section":
      return "بخش";
    case "path_hub":
      return "مسیر";
    case "pattern_cluster":
      return "الگو";
    default:
      return kind;
  }
}

export default function SiteMapView({ siteMap, selectedKey, onSelect }: Props) {
  const { nodes, edges } = useMemo(() => {
    if (!siteMap || siteMap.nodes.length === 0) {
      return { nodes: [] as Node[], edges: [] as Edge[] };
    }

    const positions = layoutTree(siteMap.nodes);
    const flowNodes: Node[] = siteMap.nodes.map((n) => {
      const pos = positions.get(n.group_key) ?? { x: 0, y: n.depth * GAP_Y };
      const repKey = n.representative_page_key;
      const selected = repKey != null && repKey === selectedKey;
      const scale = Math.min(1.4, 0.85 + n.weight / 120);
      const width = Math.round(NODE_WIDTH * scale);
      const height = Math.round(NODE_HEIGHT * scale);

      return {
        id: n.group_key,
        position: pos,
        data: {
          label: (
            <button
              type="button"
              className="sitemap-node-btn"
              disabled={!repKey}
              onClick={() => repKey && onSelect(repKey)}
            >
              <span className="sitemap-node-kind">{kindLabel(n.group_kind)}</span>
              <strong>{n.label}</strong>
              {n.url_pattern && n.group_kind === "pattern_cluster" && (
                <small className="sitemap-pattern">{n.url_pattern.replace(/^https?:\/\/[^/]+/, "")}</small>
              )}
              {n.page_type && <small>{n.page_type}</small>}
              <span className="sitemap-count-badge">{n.page_count.toLocaleString("fa-IR")} صفحه</span>
              {n.inbound_link_count > 0 && (
                <small className="sitemap-inbound">← {n.inbound_link_count.toLocaleString("fa-IR")} لینک ورودی</small>
              )}
              {n.weight > 1 && <small className="sitemap-weight">وزن {n.weight}</small>}
            </button>
          ),
        },
        style: {
          border: selected ? "2px solid #2563eb" : "1px solid #cbd5e1",
          borderRadius: 10,
          padding: 4,
          width,
          height,
          fontSize: 11,
          background: n.group_kind === "pattern_cluster" ? "#f8fafc" : "#fff",
        },
      };
    });

    const flowEdges: Edge[] = siteMap.edges.map((e, idx) => ({
      id: `e-${idx}`,
      source: e.from,
      target: e.to,
      animated: false,
      style: { strokeWidth: 1.5 },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [siteMap, selectedKey, onSelect]);

  if (!siteMap || siteMap.nodes.length === 0) {
    return (
      <p className="muted">
        نقشه سایت هنوز ساخته نشده — یک بار crawl کامل کنید یا{" "}
        <code>python scripts/inspect_data.py --reclassify</code> را اجرا کنید.
      </p>
    );
  }

  return (
    <div className="graph-panel sitemap-panel">
      <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable={false}>
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
