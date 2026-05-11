# Bambu Studio 预览与修改稿管理规则

## 核心问题

Bambu Studio 中反复 `open` 新 STL 时，可能会把新版模型继续追加到当前项目里，而不是替换旧模型。多个版本叠在同一 plate 上会导致：

- 模型重叠，看不清当前版本；
- 切片结果不可信；
- Bambu Studio 变卡，严重时接近卡死；
- 不同材料零件混在一起，例如 PETG 主骨架和 TPU 软环。

## 项目规则

1. **同一模型迭代时，只保留一个当前预览版本。**
   - 生成 `v2` 后，如果 `v1` 不再需要，应删除旧草稿文件或明确归档。
   - 不要把 `v1/v2/v3` 连续追加进同一个 Bambu Studio plate。

2. **打开新版前，优先使用新项目。**
   - 最稳做法：关闭当前 Bambu Studio 项目，再打开新版 STL/3MF。
   - 如果 Bambu Studio 已经很卡，先退出应用，再从 Finder/命令行打开最终文件。

3. **不同材料必须分项目或分 plate。**
   - PETG/PLA 主骨架与 TPU 软环不要默认放在同一个 Bambu 项目里。
   - TPU 软环通常单独打印，不走 AMS。

4. **`output/` 是临时草稿区。**
   - 每次确认终稿后，复制到 `prints/YYYY-MM/<project>/`。
   - 终稿归档后，可以清理 `output/step`、`output/stl` 里的过期草稿。

5. **打开给用户看的文件时，要说清楚当前文件名。**
   - 示例：只打开 `air_plant_hydrangea_v2_core.stl`。
   - 如果还需要软环，单独打开 `air_plant_hydrangea_v2_soft_ring_plate_6x.stl`。

## 推荐操作顺序

1. 导出新版 STL/STEP。
2. 用 Bambu Studio `--info` 检查 STL 是否水密和尺寸是否正确。
3. 清理同一模型旧版草稿，或至少不要再打开旧版。
4. 退出/新建 Bambu Studio 项目。
5. 打开当前新版 STL。
6. 用户开始打印后，立即归档到 `prints/YYYY-MM/<project>/`。

