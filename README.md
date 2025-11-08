# Crystal Generator

![crystal-thumb](https://github.com/user-attachments/assets/56993ade-dc53-4a74-8087-92e69ec4dabe)

**Author:** The French Monkey (TFMSTYLE)  
**Version:** 1.0.0  

---

## Overview

The Crystal Generator creates parametric crystal clusters composed of procedural faceted prisms.  
It can generate single crystals or grouped clusters with natural variation in tilt, height, and taper.  
Each crystal is built with adjustable facets, twist, and tip proportions to create formations ranging from realistic mineral clusters to stylized gemstones.

---

## Parameters

### Live Update
When enabled, the generator automatically rebuilds the crystal whenever a parameter is changed.  
This allows quick iteration but may slow performance for large clusters.

---

### Cluster Count
Defines the number of distinct crystal clusters generated in a circular arrangement.  
Increasing this creates multiple groups around a central point.

---

### Crystals per Cluster
Specifies how many individual crystals are included in each cluster.  
Higher values produce denser formations.

---

### Cluster Radius
Determines how widely crystals are distributed within each cluster.  
Larger radii create more spread-out, less compact groups.

---

### Crystal Base Radius
Controls the base width of each crystal shaft.  
Affects the overall thickness and perceived mass of the formation.

---

### Min Height
Sets the minimum height of individual crystals.  
Used to control size variation within a cluster.

---

### Max Height
Defines the maximum height a crystal can reach.  
Together with Min Height, it determines the height range for random generation.

---

### Body Taper
Controls how much the crystal narrows toward the tip.  
Higher values create sharper, more pointed crystals.

---

### Tip Length (Rel.)
Determines the relative proportion of the crystal length allocated to the pointed tip section.  
Larger values produce longer, more pronounced tips.

---

### Max Tilt (°)
Adds random tilting to crystals within the cluster.  
Useful for creating natural, less uniform growth formations.

---

### Facet Irregularity
Introduces slight random offsets to crystal faces and edges.  
Simulates imperfections for a more organic appearance.

---

### Twist (°)
Applies a gradual rotational twist along each crystal’s height.  
Gives the impression of torsion or growth spirals.

---

### Body Segments
Controls the number of vertical divisions in each crystal shaft.  
Higher segment counts create smoother tapering and more geometric detail.

---

### Bevel Amount
Adds a small bevel modifier to crystal edges for smoother highlights and light-catching facets.  
A value of 0 disables beveling.

---

### Seed
Defines the randomization seed for all procedural aspects of the cluster.  
Changing it produces a new formation while keeping all other parameters the same.

---

## Operators

### Generate Crystal
Creates or regenerates a crystal cluster using the current parameters.  
If an existing crystal object is selected, it will be rebuilt with updated settings.

---

### Reset Settings
Resets all crystal generator parameters to their default values.  
Preserves the live update state and automatically refreshes if active.

---

## Usage Notes

- Use **Cluster Count** and **Crystals per Cluster** together to balance density and composition.  
- Increasing **Tilt**, **Irregularity**, and **Twist** creates more organic, chaotic formations.  
- Lower **Bevel Amount** values retain sharper edges for faceted, gemstone-like appearances.  
- Enable **Live Update** for rapid iteration, but disable it when working with large clusters for better performance.  
- Applying a glass or translucent material enhances light refraction through the faceted surfaces.
