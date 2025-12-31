// app/frontend/constants/CouncilData.ts

export type CouncilType = 'standard' | 'override';

export interface Council {
  id: string;
  name: string;
  type: CouncilType;
  mapUrl?: string; // Optional URL for override maps
}

export interface Region {
  id: string;
  name: string;
  councils: Council[];
}

export const NZ_REGIONS: Region[] = [
  {
    id: 'northland',
    name: 'Northland Region',
    councils: [
       { id: 'far-north', name: 'Far North District Council', type: 'standard' },
       { id: 'whangarei', name: 'Whangarei District Council', type: 'standard' },
    ]
  },
  {
    id: 'auckland',
    name: 'Auckland Region',
    councils: [
      { id: 'aklc', name: 'Auckland Council', type: 'override', mapUrl: 'https://unitaryplanmaps.aucklandcouncil.govt.nz/upviewer/' },
    ],
  },
  {
    id: 'waikato',
    name: 'Waikato Region',
    councils: [
      { id: 'hamilton', name: 'Hamilton City Council', type: 'standard' },
      { id: 'waikato', name: 'Waikato District Council', type: 'standard' },
      { id: 'taupo', name: 'Taupō District Council', type: 'standard' },
      { id: 'thames', name: 'Thames-Coromandel District Council', type: 'standard' },
    ],
  },
  {
    id: 'bay-of-plenty',
    name: 'Bay of Plenty Region',
    councils: [
      { id: 'tauranga', name: 'Tauranga City Council', type: 'override', mapUrl: 'https://www.tauranga.govt.nz/council/maps/council-map-viewer-mapi' },
      { id: 'westernbop', name: 'Western Bay of Plenty District Council', type: 'standard' },
    ],
  },
  {
    id: 'wellington',
    name: 'Wellington Region',
    councils: [
      { id: 'wcc', name: 'Wellington City Council', type: 'override', mapUrl: 'https://data-wcc.opendata.arcgis.com/datasets/WCC::windzones/about' },
      { id: 'hutt', name: 'Hutt City Council', type: 'standard' },
      { id: 'porirua', name: 'Porirua City Council', type: 'standard' },
      { id: 'kapiti', name: 'Kāpiti Coast District Council', type: 'standard' },
    ],
  },
  {
    id: 'canterbury',
    name: 'Canterbury Region',
    councils: [
      { id: 'ccc', name: 'Christchurch City Council', type: 'override', mapUrl: 'https://mapviewer.canterburymaps.govt.nz/' },
      { id: 'selwyn', name: 'Selwyn District Council', type: 'standard' },
      { id: 'waimakariri', name: 'Waimakariri District Council', type: 'standard' },
    ],
  },
  {
    id: 'otago',
    name: 'Otago Region',
    councils: [
       { id: 'dcc', name: 'Dunedin City Council', type: 'standard' },
       { id: 'qldc', name: 'Queenstown-Lakes District Council', type: 'standard' },
    ]
  }
];
