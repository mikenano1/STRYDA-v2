// app/frontend/constants/CouncilData.ts

export type CouncilType = 'standard' | 'override';

export interface Council {
  id: string;
  name: string;
  type: CouncilType;
  mapUrl?: string; // Optional URL for override maps
}

export interface RegionGroup {
  title: string;
  data: Council[];
}

// This list is a representative sample for development. 
// The full list of 67 can be populated later.
export const NZ_COUNCILS_GROUPED: RegionGroup[] = [
  {
    title: 'Auckland Region',
    data: [
      { id: 'aklc', name: 'Auckland Council', type: 'override', mapUrl: 'https://unitaryplanmaps.aucklandcouncil.govt.nz/upviewer/' },
    ],
  },
  {
    title: 'Wellington Region',
    data: [
      { id: 'wcc', name: 'Wellington City Council', type: 'override', mapUrl: 'https://wellington.govt.nz/property-rates-and-building/building-and-resource-consents/wind-zones' },
      { id: 'hutt', name: 'Hutt City Council', type: 'standard' },
      { id: 'porirua', name: 'Porirua City Council', type: 'standard' },
      { id: 'kapiti', name: 'Kāpiti Coast District Council', type: 'standard' },
    ],
  },
  {
    title: 'Waikato Region',
    data: [
      { id: 'hamilton', name: 'Hamilton City Council', type: 'standard' },
      { id: 'waikato', name: 'Waikato District Council', type: 'standard' },
      { id: 'taupo', name: 'Taupō District Council', type: 'standard' },
      { id: 'thames', name: 'Thames-Coromandel District Council', type: 'standard' },
    ],
  },
  {
    title: 'Canterbury Region',
    data: [
      { id: 'ccc', name: 'Christchurch City Council', type: 'override', mapUrl: 'https://mapviewer.canterburymaps.govt.nz/' },
      { id: 'selwyn', name: 'Selwyn District Council', type: 'standard' },
      { id: 'waimakariri', name: 'Waimakariri District Council', type: 'standard' },
    ],
  },
  {
    title: 'Bay of Plenty Region',
    data: [
      { id: 'tauranga', name: 'Tauranga City Council', type: 'standard' },
      { id: 'westernbop', name: 'Western Bay of Plenty District Council', type: 'standard' },
    ],
  },
  {
    title: 'Northland Region',
    data: [
       { id: 'far-north', name: 'Far North District Council', type: 'standard' },
       { id: 'whangarei', name: 'Whangarei District Council', type: 'standard' },
    ]
  },
   {
    title: 'Otago Region',
    data: [
       { id: 'dcc', name: 'Dunedin City Council', type: 'standard' },
       { id: 'qldc', name: 'Queenstown-Lakes District Council', type: 'standard' },
    ]
  }
];
