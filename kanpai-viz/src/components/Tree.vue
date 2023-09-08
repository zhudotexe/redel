<script setup lang="ts">
import { KanpaiClient } from "@/kanpai/client";
import * as d3 from "d3";
import { onMounted, ref } from "vue";

const props = defineProps<{
  client: KanpaiClient;
}>();

const d3Mount = ref<HTMLElement | null>(null);

onMounted(async () => {
  await props.client.waitForReady();

  // // Compute the graph and start the force simulation.
  // const root = d3.hierarchy(
  //   props.client.rootKani,
  //   (kani) => kani?.children.map((id: string) => props.client.kaniMap.get(id)),
  // );
  // const links = root.links();
  // const nodes = root.descendants();
  //
  // const simulation = d3
  //   .forceSimulation(nodes)
  //   .force(
  //     "link",
  //     d3
  //       .forceLink(links)
  //       .id((d) => d.id)
  //       .distance(0)
  //       .strength(1),
  //   )
  //   .force("charge", d3.forceManyBody().strength(-50))
  //   .force("x", d3.forceX())
  //   .force("y", d3.forceY());

  // Create the container SVG.
  const height = 200;
  const svg = d3.select(d3Mount.value);

  svg
    .selectAll("circle")
    .data(d3.range(18))
    .join("circle")
      .attr("cx", d => 30 + d * 50)
      .attr("cy", height / 2)
      .attr("r", d => Math.random() * 20)
      .attr("fill", "#001b42");

  // // Append links.
  // const link = svg
  //   .append("g")
  //   .attr("stroke", "#999")
  //   .attr("stroke-opacity", 0.6)
  //   .selectAll("line")
  //   .data(links)
  //   .join("line");
  //
  // // Append nodes.
  // const node = svg
  //   .append("g")
  //   .attr("fill", "#fff")
  //   .attr("stroke", "#000")
  //   .attr("stroke-width", 1.5)
  //   .selectAll("circle")
  //   .data(nodes)
  //   .join("circle")
  //   .attr("fill", (d) => (d.children ? null : "#000"))
  //   .attr("stroke", (d) => (d.children ? null : "#fff"))
  //   .attr("r", 3.5);
  // // .call(drag(simulation));
  //
  // node.append("title").text((d) => d.data?.id ?? "a");
  //
  // simulation.on("tick", () => {
  //   link
  //     .attr("x1", (d) => d.source.x)
  //     .attr("y1", (d) => d.source.y)
  //     .attr("x2", (d) => d.target.x)
  //     .attr("y2", (d) => d.target.y);
  //
  //   node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
  // });
  //
  // // invalidation.then(() => simulation.stop());
});
</script>

<template>
  <svg class="d3" ref="d3Mount"></svg>
</template>

<style scoped>
.d3 {
  width: 100%;
  height: 100vh;
}
</style>
