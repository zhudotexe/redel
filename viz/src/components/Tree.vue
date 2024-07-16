<!-- @formatter:off -->
<!-- this file in JS because d3 is wack -->
<script setup>
import {RunState} from "@/kanpai/models";
import {greekLetter} from "@/utils";
import * as d3 from "d3";
import {inject, onMounted, onUnmounted, ref, watch} from "vue";

const props = defineProps(['selectedId']);
const emit = defineEmits(["nodeClicked"]);

const state = inject("state");
const d3Mount = ref(null);

// ==== style stuff ====
const colorForNode = (kaniState) => {
  // blueish if selected
  if (kaniState.id === props.selectedId)
    return "#a9e5ff";
  // if not selected, based on state
  switch (kaniState.state) {
    case RunState.running:
      return "#9af362";
    case RunState.waiting:
      return "#fffe48";
    case RunState.errored:
      return "#FF9B9B";
  }
  // stopped; gray if not root
  return kaniState.parent ? "#ddd" : "#fff";
}

const displayNameForNode = (kaniState) => {
  if (!kaniState.depth)
    return "☆";
  if (kaniState.name.endsWith("summarizer"))
    return "∑";
  return greekLetter(kaniState.name);
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
    .attr("transform", function(d) {
      return "translate(" + d.x + "," + d.y + ")";
    });

  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
}

// setup simulation
const simulation = d3.forceSimulation()
  .force("charge", d3.forceManyBody().strength(-200))
  .force("link", d3.forceLink().id(d => d.id).distance(55).strength(3))
  .force("x", d3.forceX())
  .force("y", d3.forceY())
  .on("tick", tickSimulation);

// setup canvas when the page loads
const width = 1000;
const height = 500;
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
    .selectAll("g");
});

// update data based on current state
const update = () => {
  if (!state.rootKani) return;
  let root = d3.hierarchy(
    state.rootKani,
    (kani) => kani?.children.map(id => state.kaniMap.get(id)),
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
    .join(enter => {
      // add missing nodes
      const g = enter.append("g")
        .attr("id", d => d.data.id)
        .call(drag(simulation))
        .on("click", function() {
          emit("nodeClicked", this.id);
        })
        .call(node => node.append("title").text(d => `${d.data.name} (${d.data.id})`));

      // add circle
      g.append("circle")
        .attr("r", 14)
        .attr("stroke-width", 3);

      // add text
      g.append("text")
        .style("dominant-baseline", "central")
        .style("text-anchor", "middle")
        .text(d => displayNameForNode(d.data));

      return g;
    })
      // set color based on state
      .attr("fill", d => colorForNode(d.data));

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

const updateColors = () => {
  node = node
    .attr("fill", d => colorForNode(d.data));
}

onUnmounted(() => simulation.stop());

// --- reactivity ---
// expose update methods for consumers to call
defineExpose({ update, updateColors });

// update colors when selected changes
watch(() => props.selectedId, () => updateColors());
</script>

<template>
  <svg class="d3" ref="d3Mount"></svg>
</template>

<style scoped>
</style>
