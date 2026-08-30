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
import type { SiteGraph } from "../../api/inspector";

interface Props {
  graph: SiteGraph | null;
  selectedKey?: string | null;
  onSelect: (pageKey: string) => void;
}

export default function SiteGraphView({ graph, selectedKey, onSelect }: Props) {
  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [] as Node[], edges: [] as Edge[] };
    const cols = Math.ceil(Math.sqrt(graph.nodes.length));
    const flowNodes: Node[] = graph.nodes.map((n, idx) => ({
      id: n.page_key,
      position: { x: (idx % cols) * 220, y: Math.floor(idx / cols) * 100 },
      data: {
        label: (
          <button type="button" className="graph-node-btn" onClick={() => onSelect(n.page_key)}>
            <strong>{n.section || n.page_type}</strong>
            <small>{n.title || n.url.split("/").pop()}</small>
          </button>
        ),
      },
      style: {
        border: n.page_key === selectedKey ? "2px solid #2563eb" : "1px solid #cbd5e1",
        borderRadius: 8,
        padding: 4,
        width: 180,
        fontSize: 11,
      },
    }));
    const flowEdges: Edge[] = graph.edges.map((e, idx) => ({
      id: `e-${idx}`,
      source: e.from,
      target: e.to,
      label: e.type,
    }));
    return { nodes: flowNodes, edges: flowEdges };
  }, [graph, selectedKey, onSelect]);

  if (!graph || graph.nodes.length === 0) {
    return <p className="muted">گرافی موجود نیست.</p>;
  }

  return (
    <div className="graph-panel">
      <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable={false}>
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
