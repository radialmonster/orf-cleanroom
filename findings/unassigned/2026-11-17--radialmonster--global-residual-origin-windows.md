# Global integer residual-origin sensitivity in fixed windows

Author: @radialmonster
Verified by: @radialmonster
Lead: #788
Variant: unassigned
Builds on: #32, #777

## Claim
Under the fixed free-anchor second-order family and global integer residual-origin hypothesis, four defined windows on public id 1993 leave POSSIBLE={3} only for B16 signed_digit d2; the other seven mapping/stride/depth families have empty POSSIBLE sets. All four public 5283 windows contain q>=17 and are undefined, not passes or failures. This tests a necessary range condition under an assumed token-to-row model; it does not establish physical framing, a predictor, codec or population property. The files and windows were previously exposed.

## Original evidence
On 2026-11-17 UTC the finder used `tools/free_anchor_origin.py` and `tools/free_anchor_origin_summary.py` at `caca556d1fd82c5eb4b92a4185597887b3bf3fa2`, following the fixed protocol in #32 comment 6957103461. Public CC0 raw.pixls.us id 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, and id 5283, `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`, supplied the discovery cases.

## Verification
Fresh post-lead runs on 2026-11-17 UTC reproduced both discovery producer reports byte-for-byte and evaluated the complete frozen origin grid on predeclared public CC0 id 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`, and id 6344, `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512`. Retained CC0 inventory and manifest match local hashes. Each file requests four 4096-candidate windows starting at 262144, 524288, 1048576 and 1572864; all returned in full without timeout. Each 1993/1995/6344 file has 512 completed cells; 5283 has 512 escape-undefined cells, with respective escape counts 4, 5, 9, 4. No undefined case contributes a pass. All inputs were previously studied and same-account verification is not independent-human verification. The separately written literal-bit/bounded-feasibility reference initially reached its 570-second discovery limit after three 1993 windows; a separate scoped continuation checked the fourth. Fresh original reports matched discovery byte-for-byte, so those independently checked windows were reused. The two additional files received new independent per-window checks with separate 570-second caps; all eight windows matched. The reference shared the TIFF locator and human account, capped bit conversion at each primary endpoint while independently checking count and endpoint, and did not reproduce timeout runtimes.

The discovery POSSIBLE and COMPLETE-ON-ADJUDICABLE sets are {3} for B16 signed_digit d2 and empty for the other seven families. The combined post-lead intersection, restricted to the frozen discovery POSSIBLE set, has exactly the same sets. COMPLETE-ON-ADJUDICABLE excludes the four 5283 escape windows, so {3} means not rejected on defined windows, not a pass across all files. No excluded discovery origin can re-enter; extra post-lead origin cells are descriptive controls.

The tables below report every completed cell on 1993, 1995 and 6344. Each entry is a JSON array of lane segment counts in ascending origin order: signed_digit c=-8..15 (24 entries), signed_low3 c=-4..3 (8 entries). All listed cells are `ok`; the necessary condition passes exactly when every lane has at most two segments. B16 is primary, B12 secondary. All 5283 cells are `escape`/undefined. The original c=0 cells repeat #777.

File | Start | B | mapping | d | segment-count arrays by ascending c
---: | ---: | ---: | :--- | ---: | :---
1993 | 262144 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[12],[10],[8],[6],[2],[6],[9],[10],[12],[13],[14],[16],[17],[17],[18],[19],[20]]`
1993 | 262144 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[8,8],[8,8],[7,7],[7,7],[6,6],[5,5],[4,4],[3,3],[2,1],[4,3],[5,5],[6,5],[6,6],[7,7],[7,7],[8,8],[9,9],[9,9],[10,9],[10,10],[10,10]]`
1993 | 262144 | 16 | signed_low3 | 1 | `[[12],[10],[9],[6],[2],[6],[8],[10]]`
1993 | 262144 | 16 | signed_low3 | 2 | `[[6,6],[5,5],[4,5],[3,3],[1,1],[3,3],[4,4],[5,5]]`
1993 | 262144 | 12 | signed_digit | 1 | `[[75],[71],[68],[64],[60],[55],[50],[45],[39],[32],[22],[11],[24],[32],[40],[46],[51],[56],[60],[64],[68],[72],[75],[78]]`
1993 | 262144 | 12 | signed_digit | 2 | `[[37,38],[36,36],[34,34],[32,32],[30,30],[28,28],[25,26],[23,23],[19,19],[16,16],[11,12],[6,5],[12,12],[17,16],[20,20],[23,23],[26,26],[28,28],[30,30],[32,32],[34,34],[36,36],[38,38],[40,39]]`
1993 | 262144 | 12 | signed_low3 | 1 | `[[46],[40],[33],[23],[7],[23],[32],[39]]`
1993 | 262144 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[16,17],[12,12],[4,4],[12,12],[16,16],[20,20]]`
1993 | 524288 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[12],[10],[9],[6],[3],[6],[8],[10],[12],[13],[14],[15],[16],[17],[18],[19],[20]]`
1993 | 524288 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[9,9],[8,8],[8,7],[7,7],[6,6],[6,5],[5,4],[4,3],[2,1],[3,3],[4,5],[5,6],[6,6],[7,7],[7,8],[8,8],[8,8],[9,9],[9,9],[10,10],[10,10]]`
1993 | 524288 | 16 | signed_low3 | 1 | `[[13],[11],[9],[7],[5],[4],[7],[9]]`
1993 | 524288 | 16 | signed_low3 | 2 | `[[7,7],[6,6],[5,5],[4,4],[3,3],[2,2],[4,4],[5,5]]`
1993 | 524288 | 12 | signed_digit | 1 | `[[75],[71],[68],[64],[60],[55],[51],[45],[40],[32],[24],[15],[22],[32],[39],[45],[50],[55],[60],[64],[68],[71],[75],[78]]`
1993 | 524288 | 12 | signed_digit | 2 | `[[38,38],[36,36],[34,34],[33,32],[30,30],[28,28],[26,25],[24,22],[21,20],[17,16],[13,10],[9,9],[10,12],[16,16],[19,20],[22,23],[25,26],[27,28],[30,30],[32,32],[34,34],[36,36],[37,38],[39,40]]`
1993 | 524288 | 12 | signed_low3 | 1 | `[[49],[43],[37],[28],[15],[16],[26],[35]]`
1993 | 524288 | 12 | signed_low3 | 2 | `[[25,24],[22,22],[19,18],[15,14],[9,8],[9,8],[13,14],[18,18]]`
1993 | 1048576 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[11],[10],[8],[6],[3],[7],[9],[11],[12],[13],[15],[16],[17],[18],[19],[19],[20]]`
1993 | 1048576 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[8,8],[8,8],[7,7],[7,7],[6,6],[5,5],[4,4],[3,3],[2,2],[4,4],[5,5],[6,6],[6,6],[7,7],[8,8],[8,8],[9,9],[9,9],[10,10],[10,10],[10,10]]`
1993 | 1048576 | 16 | signed_low3 | 1 | `[[12],[10],[9],[7],[3],[6],[8],[10]]`
1993 | 1048576 | 16 | signed_low3 | 2 | `[[6,6],[6,6],[5,5],[4,4],[2,2],[3,3],[4,4],[5,5]]`
1993 | 1048576 | 12 | signed_digit | 1 | `[[74],[70],[67],[63],[58],[55],[50],[44],[38],[30],[19],[13],[25],[35],[42],[47],[52],[57],[61],[65],[69],[72],[75],[79]]`
1993 | 1048576 | 12 | signed_digit | 2 | `[[37,37],[35,36],[34,34],[32,32],[30,30],[28,27],[25,25],[22,22],[19,19],[15,15],[10,10],[5,6],[13,13],[17,17],[21,21],[24,24],[26,26],[28,29],[31,31],[32,33],[35,34],[37,36],[38,38],[40,40]]`
1993 | 1048576 | 12 | signed_low3 | 1 | `[[47],[41],[34],[25],[9],[21],[31],[38]]`
1993 | 1048576 | 12 | signed_low3 | 2 | `[[23,23],[21,21],[17,17],[13,13],[5,5],[11,11],[16,16],[19,20]]`
1993 | 1572864 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[12],[10],[8],[5],[3],[7],[9],[11],[12],[13],[15],[16],[17],[18],[19],[19],[20]]`
1993 | 1572864 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[8,8],[8,8],[7,7],[7,7],[6,6],[5,5],[4,4],[3,3],[2,2],[4,3],[5,4],[6,5],[6,6],[7,7],[8,7],[8,8],[9,8],[9,9],[10,9],[10,10],[10,10]]`
1993 | 1572864 | 16 | signed_low3 | 1 | `[[12],[10],[8],[6],[3],[6],[8],[10]]`
1993 | 1572864 | 16 | signed_low3 | 2 | `[[6,6],[5,5],[4,4],[3,3],[2,2],[3,3],[4,4],[5,5]]`
1993 | 1572864 | 12 | signed_digit | 1 | `[[74],[70],[67],[63],[59],[54],[49],[44],[38],[30],[19],[12],[25],[34],[41],[47],[52],[57],[61],[65],[69],[72],[76],[79]]`
1993 | 1572864 | 12 | signed_digit | 2 | `[[37,38],[35,36],[33,34],[31,32],[29,30],[27,28],[25,25],[22,23],[19,20],[15,16],[9,11],[7,7],[14,11],[18,16],[21,20],[24,23],[27,26],[29,28],[31,30],[33,33],[35,34],[37,36],[38,38],[40,39]]`
1993 | 1572864 | 12 | signed_low3 | 1 | `[[46],[40],[32],[23],[12],[22],[32],[39]]`
1993 | 1572864 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[17,16],[11,12],[6,7],[11,11],[16,16],[20,20]]`
1995 | 262144 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[12],[10],[8],[6],[2],[6],[8],[10],[12],[13],[14],[15],[16],[17],[18],[19],[20]]`
1995 | 262144 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[8,9],[8,8],[7,7],[7,7],[6,6],[5,5],[5,4],[3,3],[1,1],[3,3],[4,5],[5,5],[6,6],[7,7],[7,7],[8,8],[9,8],[9,9],[9,9],[10,10],[10,10]]`
1995 | 262144 | 16 | signed_low3 | 1 | `[[12],[10],[9],[6],[1],[6],[8],[10]]`
1995 | 262144 | 16 | signed_low3 | 2 | `[[6,6],[5,5],[5,4],[3,3],[1,1],[3,3],[4,5],[5,5]]`
1995 | 262144 | 12 | signed_digit | 1 | `[[75],[71],[68],[64],[60],[55],[51],[45],[39],[32],[22],[10],[22],[32],[40],[45],[51],[56],[60],[64],[68],[72],[75],[78]]`
1995 | 262144 | 12 | signed_digit | 2 | `[[38,38],[36,36],[34,34],[32,32],[30,30],[28,28],[25,26],[23,23],[20,20],[16,16],[12,12],[5,4],[12,12],[16,16],[20,20],[23,23],[26,26],[28,28],[30,30],[33,32],[34,34],[36,36],[38,38],[39,39]]`
1995 | 262144 | 12 | signed_low3 | 1 | `[[46],[40],[33],[23],[5],[23],[32],[39]]`
1995 | 262144 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[17,17],[12,12],[3,3],[12,12],[16,16],[20,20]]`
1995 | 524288 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[12],[10],[8],[6],[3],[7],[9],[11],[12],[13],[15],[16],[17],[18],[19],[19],[20]]`
1995 | 524288 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[8,8],[8,8],[7,7],[7,7],[6,6],[5,5],[4,4],[3,3],[2,2],[4,3],[5,5],[6,5],[6,6],[7,7],[8,8],[8,8],[9,9],[9,9],[10,9],[10,10],[10,10]]`
1995 | 524288 | 16 | signed_low3 | 1 | `[[12],[10],[9],[6],[1],[6],[8],[10]]`
1995 | 524288 | 16 | signed_low3 | 2 | `[[6,6],[5,5],[4,5],[3,3],[1,1],[3,3],[5,4],[5,5]]`
1995 | 524288 | 12 | signed_digit | 1 | `[[74],[71],[67],[64],[59],[55],[50],[44],[38],[30],[20],[12],[25],[34],[41],[47],[52],[57],[61],[65],[68],[72],[76],[79]]`
1995 | 524288 | 12 | signed_digit | 2 | `[[37,37],[35,36],[33,34],[32,32],[29,30],[27,28],[25,25],[22,22],[19,20],[15,16],[9,10],[7,7],[13,12],[18,16],[21,20],[24,23],[26,26],[29,28],[31,30],[33,33],[35,34],[37,36],[38,38],[40,40]]`
1995 | 524288 | 12 | signed_low3 | 1 | `[[46],[40],[32],[23],[4],[23],[32],[39]]`
1995 | 524288 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[16,17],[12,12],[2,4],[12,11],[17,16],[20,20]]`
1995 | 1048576 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[12],[10],[8],[6],[3],[7],[9],[11],[12],[13],[15],[16],[17],[18],[19],[19],[20]]`
1995 | 1048576 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[8,8],[8,8],[7,7],[7,7],[6,6],[5,5],[4,4],[3,3],[1,1],[4,3],[5,5],[5,6],[6,6],[7,7],[8,8],[8,8],[9,9],[9,9],[10,10],[10,10],[10,10]]`
1995 | 1048576 | 16 | signed_low3 | 1 | `[[12],[10],[8],[6],[2],[6],[9],[10]]`
1995 | 1048576 | 16 | signed_low3 | 2 | `[[6,6],[5,5],[5,5],[3,3],[1,1],[3,3],[4,4],[5,5]]`
1995 | 1048576 | 12 | signed_digit | 1 | `[[74],[71],[67],[63],[60],[55],[50],[44],[38],[30],[21],[14],[26],[33],[41],[46],[52],[57],[61],[65],[69],[72],[75],[79]]`
1995 | 1048576 | 12 | signed_digit | 2 | `[[38,37],[36,36],[34,34],[32,32],[30,30],[28,27],[25,25],[23,23],[20,19],[16,16],[11,11],[6,7],[12,13],[17,17],[20,21],[24,24],[26,26],[29,29],[31,30],[33,33],[35,34],[36,36],[38,38],[40,40]]`
1995 | 1048576 | 12 | signed_low3 | 1 | `[[46],[40],[33],[23],[7],[23],[32],[39]]`
1995 | 1048576 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[17,17],[12,12],[4,4],[11,11],[16,16],[20,20]]`
1995 | 1572864 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[15],[14],[13],[11],[10],[8],[6],[3],[7],[9],[11],[12],[13],[15],[16],[17],[18],[19],[19],[20]]`
1995 | 1572864 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[8,8],[8,8],[7,7],[7,7],[6,6],[5,5],[4,4],[3,3],[2,2],[3,4],[5,5],[5,6],[6,6],[7,7],[7,8],[8,8],[9,9],[9,9],[9,10],[10,10],[10,10]]`
1995 | 1572864 | 16 | signed_low3 | 1 | `[[12],[10],[9],[6],[2],[6],[8],[10]]`
1995 | 1572864 | 16 | signed_low3 | 2 | `[[6,6],[5,5],[5,5],[3,3],[1,1],[3,3],[4,4],[5,5]]`
1995 | 1572864 | 12 | signed_digit | 1 | `[[74],[71],[67],[63],[59],[54],[49],[44],[38],[31],[20],[12],[25],[34],[41],[46],[52],[57],[61],[65],[69],[72],[76],[79]]`
1995 | 1572864 | 12 | signed_digit | 2 | `[[37,37],[36,35],[34,34],[32,32],[30,29],[28,27],[25,25],[23,22],[19,19],[16,15],[11,10],[6,8],[12,13],[17,18],[20,21],[23,24],[26,27],[28,29],[31,31],[32,33],[34,35],[36,37],[38,38],[40,40]]`
1995 | 1572864 | 12 | signed_low3 | 1 | `[[46],[40],[33],[23],[5],[22],[32],[39]]`
1995 | 1572864 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[17,16],[12,12],[3,3],[11,12],[16,16],[20,20]]`
6344 | 262144 | 16 | signed_digit | 1 | `[[19],[19],[18],[17],[16],[14],[13],[12],[10],[9],[7],[3],[6],[8],[10],[11],[13],[14],[15],[16],[17],[18],[19],[20]]`
6344 | 262144 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[9,9],[8,8],[8,7],[7,7],[6,6],[6,5],[5,5],[3,3],[2,2],[3,3],[4,4],[5,5],[6,6],[7,7],[7,7],[8,8],[8,8],[9,9],[9,9],[10,10],[10,10]]`
6344 | 262144 | 16 | signed_low3 | 1 | `[[12],[10],[9],[7],[3],[6],[8],[10]]`
6344 | 262144 | 16 | signed_low3 | 2 | `[[6,6],[6,5],[5,5],[4,4],[2,2],[3,3],[4,4],[5,5]]`
6344 | 262144 | 12 | signed_digit | 1 | `[[75],[72],[68],[64],[61],[57],[51],[46],[40],[34],[24],[13],[20],[31],[38],[44],[49],[54],[59],[63],[67],[71],[74],[78]]`
6344 | 262144 | 12 | signed_digit | 2 | `[[38,38],[36,36],[34,34],[33,32],[31,30],[28,28],[26,26],[24,23],[21,20],[17,16],[12,13],[6,8],[10,11],[16,16],[19,19],[22,22],[25,25],[28,28],[30,29],[32,32],[34,34],[36,36],[37,37],[39,39]]`
6344 | 262144 | 12 | signed_low3 | 1 | `[[46],[41],[33],[24],[13],[20],[31],[38]]`
6344 | 262144 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[17,17],[13,12],[6,6],[11,11],[15,16],[19,20]]`
6344 | 524288 | 16 | signed_digit | 1 | `[[19],[18],[18],[17],[16],[15],[13],[12],[10],[8],[6],[3],[6],[8],[10],[12],[13],[14],[15],[16],[17],[18],[19],[20]]`
6344 | 524288 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[9,8],[8,8],[8,8],[7,7],[6,6],[6,6],[5,4],[4,3],[1,2],[3,3],[4,4],[5,5],[6,6],[7,7],[7,7],[8,8],[8,8],[9,9],[9,9],[10,10],[10,10]]`
6344 | 524288 | 16 | signed_low3 | 1 | `[[12],[10],[8],[6],[4],[6],[8],[10]]`
6344 | 524288 | 16 | signed_low3 | 2 | `[[6,6],[5,5],[4,4],[3,3],[2,1],[3,3],[4,5],[5,5]]`
6344 | 524288 | 12 | signed_digit | 1 | `[[75],[72],[68],[64],[60],[56],[51],[46],[40],[32],[24],[12],[21],[31],[39],[44],[50],[55],[59],[63],[67],[71],[74],[78]]`
6344 | 524288 | 12 | signed_digit | 2 | `[[38,38],[36,36],[35,34],[32,32],[31,31],[28,29],[26,26],[23,24],[20,20],[17,17],[12,12],[8,9],[10,11],[16,16],[20,20],[22,23],[25,25],[27,28],[30,30],[32,32],[34,34],[36,36],[37,37],[39,39]]`
6344 | 524288 | 12 | signed_low3 | 1 | `[[45],[39],[32],[23],[13],[23],[32],[39]]`
6344 | 524288 | 12 | signed_low3 | 2 | `[[23,23],[20,20],[16,16],[11,11],[6,6],[11,11],[16,16],[20,20]]`
6344 | 1048576 | 16 | signed_digit | 1 | `[[19],[19],[18],[17],[16],[15],[13],[12],[11],[9],[7],[4],[5],[8],[10],[11],[13],[14],[15],[16],[17],[18],[19],[20]]`
6344 | 1048576 | 16 | signed_digit | 2 | `[[10,10],[9,10],[9,9],[9,9],[8,8],[8,8],[7,7],[6,6],[6,6],[5,5],[3,4],[2,2],[3,3],[4,4],[5,5],[6,6],[7,7],[7,7],[8,8],[8,8],[9,9],[9,9],[10,10],[10,10]]`
6344 | 1048576 | 16 | signed_low3 | 1 | `[[12],[11],[9],[7],[4],[5],[8],[10]]`
6344 | 1048576 | 16 | signed_low3 | 2 | `[[6,6],[6,6],[5,5],[4,4],[2,2],[3,3],[4,4],[5,5]]`
6344 | 1048576 | 12 | signed_digit | 1 | `[[76],[72],[69],[65],[61],[57],[52],[47],[41],[34],[25],[13],[19],[29],[38],[44],[50],[54],[59],[63],[67],[70],[74],[77]]`
6344 | 1048576 | 12 | signed_digit | 2 | `[[38,38],[36,37],[34,35],[32,33],[31,31],[28,29],[26,27],[23,24],[21,21],[17,18],[13,14],[7,8],[10,9],[16,15],[20,19],[23,22],[25,24],[28,27],[30,29],[32,31],[34,33],[36,35],[38,37],[39,39]]`
6344 | 1048576 | 12 | signed_low3 | 1 | `[[46],[41],[34],[25],[14],[20],[30],[38]]`
6344 | 1048576 | 12 | signed_low3 | 2 | `[[24,24],[21,21],[17,17],[13,13],[7,7],[10,9],[15,15],[19,19]]`
6344 | 1572864 | 16 | signed_digit | 1 | `[[19],[18],[17],[16],[16],[14],[13],[12],[10],[8],[6],[3],[6],[8],[10],[12],[13],[14],[15],[16],[17],[18],[19],[20]]`
6344 | 1572864 | 16 | signed_digit | 2 | `[[10,10],[9,9],[9,9],[9,8],[8,8],[7,7],[7,7],[6,6],[5,5],[5,4],[4,3],[1,2],[3,3],[4,5],[5,5],[6,6],[7,7],[7,7],[8,8],[8,9],[9,9],[9,9],[10,10],[10,10]]`
6344 | 1572864 | 16 | signed_low3 | 1 | `[[12],[11],[9],[7],[4],[4],[7],[9]]`
6344 | 1572864 | 16 | signed_low3 | 2 | `[[7,6],[6,6],[5,5],[4,4],[2,2],[2,3],[4,4],[5,5]]`
6344 | 1572864 | 12 | signed_digit | 1 | `[[75],[72],[68],[64],[60],[55],[50],[45],[39],[32],[22],[14],[22],[32],[39],[45],[51],[55],[60],[64],[68],[72],[75],[78]]`
6344 | 1572864 | 12 | signed_digit | 2 | `[[38,37],[36,36],[34,34],[32,32],[30,30],[28,28],[26,26],[23,23],[20,20],[17,16],[12,11],[6,7],[11,12],[16,16],[20,20],[23,23],[25,26],[28,28],[30,30],[32,33],[34,34],[36,36],[38,37],[39,40]]`
6344 | 1572864 | 12 | signed_low3 | 1 | `[[48],[42],[35],[27],[16],[16],[28],[36]]`
6344 | 1572864 | 12 | signed_low3 | 2 | `[[24,24],[22,21],[18,18],[14,13],[8,8],[8,8],[14,14],[18,18]]`

The literal MSB-first candidate parse starts at payload bit zero as q zeros, a stop bit and five suffix bits, with no extra escape skip. The signed_digit map is `4*(s>>3)+(s&3)-8*((s>>2)&1)` and signed_low3 is `(s&7)-8` if `s&4`, else `s&7`; subtract the same integer c in every window and file of a family. Each contiguous lane segment has two unrestricted integer initial values in [0,2**B-1], ignores its first two residuals and then uses `x[i]=2*x[i-1]-x[i-2]+map(s)-c`, without wrap, clamp or adaptation. d2 lanes choose independent, possibly incompatible breaks. Unknowns do not eliminate an origin; a completed lane needing more than two segments is a known failure even if another lane times out.

Outside the specified integer map alphabet, all residuals have one strict sign. A 2048-point d2 lane split into at most two segments has a segment of at least 1024 points; three equally spaced points 511 apart then have signed second-difference magnitude at least 511^2=261121, exceeding the maximum 2*65535=131070 permitted by B16 values. The longer d1 lane and narrower B12 also satisfy this necessary bound. This only excludes outside-alphabet integer origins within the declared model; noninteger/scaled mappings, other budgets and syntax remain open. Existing candidate-token counts already challenge the literal one-token-per-site row mapping. No physical framing, causal, calibrated-significance or population claim follows.

## Reproduce
After reading the source/imports and matching local files to retained CC0 hashes, run from the named commit for each listed file and save the aggregate JSON; use a hard 600-second per-file guard:

    python -I -B tools/free_anchor_origin.py --sample ID PUBLIC_NAME PATH_TO_CC0_FILE
    python -I -B tools/free_anchor_origin_summary.py --stage discovery --discovery DISCOVERY_1993.json --discovery DISCOVERY_5283.json
    python -I -B tools/free_anchor_origin_summary.py --stage verification --discovery DISCOVERY_1993.json --discovery DISCOVERY_5283.json --postlead REPEAT_1993.json --postlead REPEAT_5283.json --postlead REPORT_1995.json --postlead REPORT_6344.json

The producer uses a cooperative 20-second per-case and 570-second per-file budget. Preserve every unknown, failed, short or timed-out case rather than substituting data. Post-lead conclusions remain restricted to the frozen discovery POSSIBLE set.
