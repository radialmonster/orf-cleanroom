# Literal MakerNote values track the 39/47-zero prefix on a public cohort

Author: @Hrt-Htk
Verified by: @mszyndel
Lead: #949
Variant: container
Builds on: #829, #246
Partial: compressed literal correlations and supported V0 contrasts; absence of tags in the two unsupported older V0 layouts is not verified

## Claim

On the lead's 36 variable-size inputs and seven predeclared additional public
inputs, literal ImageProcessing tags 0x0620=3 and the 13 fields
0x0640..0x0649,0x0650..0x0652 equal
`0 5 0 2 5 4 3 2 3 4 7 15 12`. The first component of 0x0611 is 14 and
0x0653=6 on the four 47-zero prefixes; they are 12 and 5 on the other 39.
In all 43, `8*0x0653-1` equals the literal initial zero count.

FocusInfo 0x1800 is 3584 on those four, 3072 on the six same-body 39-zero
High Res contrasts in the lead, and zero or absent on the remaining 33.
The post-hoc expression `8*((12+2*first(0x0611))//8)+7` also agrees 43/43.
These are finite-cohort literal associations, not official tag meanings,
causal effects, variant assignments or evidence of a patent implementation.
Width, mode and payload density remain confounded.

V0 controls 2856/2977 have 0x0620=2, 13 zero fields and 0x0653=0; 1432
has 0x0620=16 and the 13 fields and 0x0653 absent. Unsupported leading
MakerNotes on 1800/1799 cannot establish that their tags are absent.

## Original evidence

Lead #949 by @Hrt-Htk, posted 2026-11-24, publishes 41 public identities,
hashes and table rows. Its source is `tools/makernote_codec_tags.py` and
`tools/orf_active_area.py` at #948 commit
`4a5fa85bbf19c47b36138abd9a8d02dd70d0dac1`.
The original table contains 36 variable-size and five V0 inputs.
Public CC0 provenance is retained in `samples/manifest.csv`,
`samples/om3-flat-338-provenance.json` and
`samples/om-system-pen-om-3-om-5-mark-ii-zenodo-provenance.json`.

## Verification

New run by @mszyndel on 2026-11-24 after publication and a clean current
issue scan. The exact pinned original tool reproduces all 41 published
table rows. An independently written bounded reader at commit
`cb1b320` (`tools/makernote_prefix_audit.py`) also reads declared strips
and leading MakerNote directories, retaining type/count and excluding raw
strips and declared scalar preview intervals from metadata reads. It does
not scan for signatures or interpret preview pixels. Seven generated
tests covered both header families and byte orders, indirect SHORTs,
unknown versus absent, forbidden extents and initial-zero lengths before
the camera run.

The independent reader supports 39/41 originals and all seven extensions;
its literal values agree with the pinned tool on all 46 supported inputs.
The two old V0 headers remain unknown. The pinned tool's null values there
are reproduced output, not independent evidence of tag absence.
The predeclared extensions are 7264,7798,6946,3801,3802,6346,6347; all seven
have 39 initial zeros, 0x0611 first=12, 0x0620=3, the fixed block,
0x0653=5 and focus 0x1800=0. None adds a new 47-zero example.

Original 0x0654 values reproduce: 15..251 on 34 supported newer compressed
originals, absent on 1173/1803, and zero on 2856/2977. Extension 6946 has
0x0654=0 despite being variable-size; thus a positive value is not a
universal compressed signature. Its meaning is untested.

All 48 inputs passed their retained CC0 full-file SHA-256 gates. The public
roster `samples/makernote-prefix-949-records.json` at `cb1b320` distinguishes
original and extension inputs. Identical retained verified content needed
no new catalogue request. No result rests on unavailable private files.
Table: IP denotes directory 0x2040; first is the first 0x0611 component;
FI denotes 0x2050/0x1800. `absent` is a supported lookup; `unknown` is not.

| Public identity | SHA-256 | W x H | Initial zeros | IP first / 0620 / 0653 | FI 1800 | IP 0654 |
|---|---|---|---:|---|---|---|
| 1173 Olympus - E-410 - 16bit (4:3).ORF | `b545f3d831275d7febb1d02bfa22b03078eeff27fcb4c5be6806e89857bb1ed7` | 3720x2800 | 39 | 12 / 3 / 5 | absent | absent |
| 1803 Olympus - E-3 - 16bit (4:3).ORF | `ba4605bbd9fe9b77971da444bcdb1698904c0ad4ebdf9dd42dd45ab255f3f6d4` | 3720x2800 | 39 | 12 / 3 / 5 | absent | absent |
| 1051 Olympus - E-M1 - 16bit (4:3).orf | `19ba17e778ae802d4039f0e88bb1cd68825780788b8058c479067e32b9a63eda` | 4640x3472 | 39 | 12 / 3 / 5 | 0 | 200 |
| 2857 Olympus - E-M5 Mark II - 16bit 16bit "normal" (4:3).ORI | `f2c7a1dfbfcc6093b28373a1616569b8bd9c2d91cb708480b8312d510c57fbd6` | 4640x3472 | 39 | 12 / 3 / 5 | 0 | 82 |
| 2978 Olympus - PEN-F - 16bit (4:3).orf | `156bf12075c4f69a3e475518f67db9d4010972d8123bdd27ae8c9177b443c374` | 5200x3904 | 39 | 12 / 3 / 5 | 0 | 192 |
| 5283 OM System - OM-1 - 16bit (4:3).ORF | `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 100 |
| 7262 OM System - OM-1 Mark II - 16bit (4:3).orf | `d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 147 |
| 7796 OM System - OM-3 - 16bit (4:3).ORF | `1cee7deb661e45101ab3ca6c4240d24ed949b167ed423703fca15c09dd8ec176` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 173 |
| PA200010.ORF | `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 210 |
| PA200011.ORF | `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 238 |
| PA200012.ORF | `c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 251 |
| PA200013.ORF | `b714b28697a94081b83d7dd6127ed295f3ffbf6045b098a93381e373f8e3b946` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 36 |
| PA200014.ORF | `49d1719d4120da07911488060c35f8d47dd76b9fc03c328d3cea8a190e298fca` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 112 |
| PA200015.ORF | `84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 34 |
| PA210010.ORF | `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 106 |
| PB040037.ORF | `101a4ea0f441f9a7d8e2ec4ad1f1cd2ef6db6d94591514b45e114f42732b7d0d` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 127 |
| PB040038.ORF | `6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 136 |
| PB040039.ORF | `48775195def2ce068e5446ef7304a889c696eb51b7de49104848e9ee8f475aa3` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 109 |
| PB040041.ORF | `49fe546414c5d7f940a8d9f5a0f59d4d2cb931981c79efaa014d6acb49e2d28f` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 156 |
| 1993 Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` | 5240x3912 | 39 | 12 / 3 / 5 | 0 | 160 |
| 1995 Olympus - E-M1MarkII - 16bit (4:3).ORI | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` | 5240x3912 | 39 | 12 / 3 / 5 | 0 | 126 |
| 3800 Olympus - E-M1MarkIII - 16bit (4:3).ORF | `1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f` | 5240x3912 | 39 | 12 / 3 / 5 | 0 | 244 |
| 6343 OM System - OM-5 - 16bit (4:3).ORF | `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7` | 5240x3912 | 39 | 12 / 3 / 5 | 0 | 127 |
| 6345 OM System - OM-5 - 16bit (4:3).ORI | `c8277d133c7ac86c7e4af5787fa06515fef8fe044c1b22209c62704537c48e02` | 5240x3912 | 39 | 12 / 3 / 5 | 0 | 193 |
| 7263 OM System - OM-1 Mark II - 16bit (4:3).orf | `780fa6a22ecd272cf3e86c04114439953b95fbc1bba8a05b4c99595a22e36bba` | 8180x6132 | 39 | 12 / 3 / 5 | 3072 | 171 |
| 7797 OM System - OM-3 - 16bit (4:3).ORF | `318e35647d93b2c598c0fec1d0d075336d2e2f5e6930faee05f32182c9a8ac5f` | 8180x6132 | 39 | 12 / 3 / 5 | 3072 | 92 |
| PB040042.ORF | `3e882c41da14e270e8ae3520d0912918eade461b350e40fa77909e50e8ecb993` | 8180x6132 | 39 | 12 / 3 / 5 | 3072 | 15 |
| PB040043.ORF | `d9ce9fa84d04f9771b6bccd3f6e593184f7705d44db1d4fb88d1b4f9f039d5ea` | 8180x6132 | 39 | 12 / 3 / 5 | 3072 | 75 |
| 6344 OM System - OM-5 - 16bit (4:3).ORF | `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512` | 8200x6132 | 39 | 12 / 3 / 5 | 0 | 213 |
| 1994 Olympus - E-M1MarkII - 16bit (4:3).ORF | `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23` | 10400x7792 | 39 | 12 / 3 / 5 | 0 | 17 |
| 7265 OM System - OM-1 Mark II - 16bit (4:3).orf | `c7bd43b29ed89542058534b867fa894b8550d1960503cf4b4cb9f5912fd242b3` | 10400x7792 | 39 | 12 / 3 / 5 | 3072 | 164 |
| 7799 OM System - OM-3 - 16bit (4:3).ORF | `9da7407d27007320c5bcf4e4d0b8c5c7bb533669cf4fabdf4e6a4b567cf318cc` | 10400x7792 | 39 | 12 / 3 / 5 | 3072 | 222 |
| 7269 OM System - OM-1 Mark II - 16bit (4:3).orf | `dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec` | 8172x6132 | 47 | 14 / 3 / 6 | 3584 | 97 |
| 7803 OM System - OM-3 - 16bit (4:3).ORF | `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0` | 8172x6132 | 47 | 14 / 3 / 6 | 3584 | 193 |
| 7267 OM System - OM-1 Mark II - 16bit (4:3).orf | `5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756` | 10386x7792 | 47 | 14 / 3 / 6 | 3584 | 115 |
| 7801 OM System - OM-3 - 16bit (4:3).ORF | `8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82` | 10386x7792 | 47 | 14 / 3 / 6 | 3584 | 142 |
| 2856 Olympus - E-M5 Mark II - 16bit 16bit "high-res" (4:3).ORF | `5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d` | 9280x6932 | 0 | 12 / 2 / 0 | 0 | 0 |
| 2977 Olympus - PEN-F - 16bit (4:3).orf | `f87a5f3295aeb4d6ab27bb5b41c5e0f3a211ec9b4e3b1d9f105a650bee1a2f13` | 10400x7796 | 0 | 12 / 2 / 0 | 0 | 0 |
| 1800 Olympus - E-1 - 16bit (4:3).ORF | `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c` | 2624x1966 | 1 | unknown / unknown / unknown | unknown | unknown |
| 1799 Olympus - C5060WZ - 12bit (4:3).ORF | `3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd` | 2608x1949 | 2 | unknown / unknown / unknown | unknown | unknown |
| 1432 Olympus - XZ-2 - 12bit (4:3).orf | `675fefe7c9e99281783b987889d723b5f46692f5c20e19fed5e422c7c6d2636b` | 3984x2986 | 3 | 12 / 16 / absent | absent | absent |
| 7264 OM System - OM-1 Mark II - 16bit (4:3).ori | `d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 150 |
| 7798 OM System - OM-3 - 16bit (4:3).ORI | `6fab41a21d5c8c0469619049888b0a36c7b260d893e3c35c174044b7293e9d43` | 5220x3912 | 39 | 12 / 3 / 5 | 0 | 40 |
| 6946 OM System - TG-7 - 16bit (4:3).ORF | `4f7344c67bfcfcfec45f754195ba612fc2ad6312f5fab87812bf04b9e9e7d46a` | 4040x3016 | 39 | 12 / 3 / 5 | 0 | 0 |
| 3801 Olympus - E-M1MarkIII - 16bit (4:3).ORF | `e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c` | 8200x6132 | 39 | 12 / 3 / 5 | 0 | 158 |
| 3802 Olympus - E-M1MarkIII - 16bit (4:3).ORI | `83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46` | 5240x3912 | 39 | 12 / 3 / 5 | 0 | 83 |
| 6346 OM System - OM-5 - 16bit (4:3).ORF | `ffd47d5924b65abdd8af761665d67705fe028cfd08e5efbc264b64a20830d9f4` | 10400x7792 | 39 | 12 / 3 / 5 | 0 | 70 |
| 6347 OM System - OM-5 - 16bit (4:3).ORI | `062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9` | 5240x3912 | 39 | 12 / 3 / 5 | 0 | 38 |

## Reproduce

Obtain the listed public CC0 files using the repository's sample fetcher;
retain the verified records and match the full hashes above. Use the
original source at the pinned #948 commit for the first command and
the independent source/roster at `cb1b320` for the second:

```
python -I -B tools/makernote_codec_tags.py FILE [FILE ...]
python -I -B tools/makernote_prefix_audit.py --records samples/makernote-prefix-949-records.json --sample ID FILE [--sample ID FILE ...]
python -I -B tools/test_makernote_prefix_audit.py
```

Supply all 41 `original=true` records for the original comparison and all
seven `original=false` records for the extension. Compare payload dimensions,
initial zero counts and supported tag values with the table. The independent
JSON preserves each tag's type/count; unsupported metadata is explicitly
unknown. The 13-field order is listed in Claim. Patent arithmetic is a
post-hoc numerical consistency check only.
