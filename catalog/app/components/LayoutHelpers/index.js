/* Simple Layout Helpers */
import styled from 'styled-components';

import { breaks, rowVSpace } from 'constants/style';

export const BigSkip = styled.div`
  margin-bottom: 8em;
`;

export function breakUnder(size, css) {
  const max = breaks[size] - 1;
  return (
    `@media (max-width:${max}px) {
      ${css}
    }`
  );
}

export const CenterText = styled.div`
  text-align: center;
`;

// for use with material-ui, hence camelCase properties
// to work, this sometimes requires that a width be set
export const ellipsisObj = {
  display: 'block',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};

/* Pad - simple padding box */
const pad = '2em';
const smPad = '.8em';
export const Pad = styled.div`
  padding-bottom: ${(props) => props.bottom ? pad : 0};
  padding-left: ${(props) => props.left ? pad : 0};
  padding-right: ${(props) => props.right ? pad : 0};
  /* account for h1 margin-top */
  padding-top: ${(props) => props.top ? smPad : 0};
`;

// for unboxing content; get for full-bleed pages
export const UnPad = styled.div`
  margin-bottom: -${pad};
  margin-left: -${pad};
  margin-right: -${pad};
  margin-top: -${smPad};
`;

export const HCenter = styled.div`
  & > div, & > iframe {
    display: block;
    margin: 0 auto;
  }
`;

/* SpaceRows - Add vertical space between stacked rows */
export const SpaceRows = styled.div`
  > .row {
    margin-bottom: ${rowVSpace};
  }
`;

/* Scroll - Simple way to prevent layout overflow */
export const Scroll = styled.div`
  overflow: auto;
`;

export const Skip = styled.div`
  height: ${(props) => props.height}
`;

Skip.defaultProps = {
  height: '2em',
};
