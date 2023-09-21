<!-- @formatter:off -->
<!-- this file in JS because d3 is wack -->
<script setup>
import { RunState } from "@/kanpai/models";
import * as d3 from "d3";
import {inject, onMounted, onUnmounted, ref, watch} from "vue";

const emit = defineEmits(["nodeClicked"]);

const client = inject("client");
const d3Mount = ref(null);

// ==== style stuff ====
const colorForState = (state) => {
  switch (state) {
    case RunState.stopped:
      return "#fff";
    case RunState.running:
      return "#9af362";
    case RunState.waiting:
      return "#fffe48";
    case RunState.errored:
      return "#FF9B9B";
    default:
      return "#fff";
  }
}

// ==== d3 stuff ====
// setup
let svg, link, node;

const drag = simulation => {
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
}

const tickSimulation = () => {
  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);

  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
}

// setup simulation
const simulation = d3.forceSimulation()
  .force("charge", d3.forceManyBody().strength(-50))
  .force("link", d3.forceLink().id(d => d.id).distance(15).strength(1))
  .force("x", d3.forceX())
  .force("y", d3.forceY())
  .on("tick", tickSimulation);

// setup canvas when the page loads
const width = 900;
const height = 400;
onMounted(() => {
  // Create the container SVG.
  svg = d3.select(d3Mount.value)
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("style", "max-width: 100%; height: auto;");

  // create shape groups
  link = svg
    .append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
    .selectAll("line");

  node = svg
    .append("g")
      .attr("fill", "#fff")
      .attr("stroke", "#000")
      .attr("stroke-width", 1.5)
    .selectAll("circle");
});

// update data based on current state of client
const update = () => {
  let root = d3.hierarchy(
    client.rootKani,
    (kani) => kani?.children.map(id => client.kaniMap.get(id)),
  );
  let links = root.links();
  let nodes = root.descendants();

  // Make a shallow copy to protect against mutation, while
  // recycling old nodes to preserve position and velocity.
  const old = new Map(node.data().map(d => [d.data.id, d]));
  // weird hack to make the links ref the right nodes
  nodes = nodes.map(d => ({...old.get(d.data.id), ...d, id: d.data.id}));
  links = links.map(d => ({source: d.source.data.id, target: d.target.data.id}));

  // update node group
  node = node
    .data(nodes, d => d.id)
    .join(enter => enter
      // add missing nodes
      .append("circle")
        .attr("id", d => d.data.id)
        .attr("r", 5.5)
        .call(drag(simulation))
        .call(node => node.append("title").text(d => d.data.id))
        .on("click", function() {
          emit("nodeClicked", this.id);
        }))
      // set color based on state
      .attr("fill", d => colorForState(d.data.state));

  // update link group
  link = link
    .data(links)
    .join("line");

  // update simulation
  simulation.nodes(nodes);
  simulation.force("link").links(links);
  simulation.alpha(0.3).restart().tick();
  tickSimulation(); // render now!
};

onUnmounted(() => simulation.stop());

// --- reactivity ---
// update on load
onMounted(async () => {
  await client.waitForReady();
  update();
});

// update when the app state changes
watch(client.kaniMap, () => update());
</script>

<template>
  <svg class="d3" ref="d3Mount"></svg>
</template>

<style scoped>
</style>
