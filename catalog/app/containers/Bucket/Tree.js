import { basename } from 'path';

import PT from 'prop-types';
import * as React from 'react';
import { Link } from 'react-router-dom';
import * as RC from 'recompose';
import Button from '@material-ui/core/Button';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import ContentWindow from 'components/ContentWindow';
import { Signer } from 'utils/AWS';
import * as NamedRoutes from 'utils/NamedRoutes';
import {
  getBreadCrumbs,
  isDir,
} from 'utils/s3paths';
import { composeComponent } from 'utils/reactTools';

import Listing from './Listing';
import Summary from './Summary';


const BreadCrumbs = composeComponent('Bucket.Tree.BreadCrumbs',
  RC.setPropTypes({
    bucket: PT.string.isRequired,
    path: PT.string.isRequired,
  }),
  withStyles(({ typography }) => ({
    root: {
      fontWeight: typography.fontWeightRegular,
    },
  })),
  NamedRoutes.inject(),
  ({ classes, bucket, path, urls }) => (
    <Typography variant="h6" className={classes.root}>
      {path
        ? <Link to={urls.bucketTree(bucket)}>{bucket}</Link>
        : bucket
      }
      {getBreadCrumbs(path).map((b) => (
        <span key={b}>
          <span> / </span>
          {b === path
            ? basename(b)
            : <Link to={urls.bucketTree(bucket, b)}>{basename(b)}</Link>
          }
        </span>
      ))}
    </Typography>
  ));

export default composeComponent('Bucket.Tree',
  Signer.inject(),
  withStyles(({ spacing: { unit } }) => ({
    topBar: {
      alignItems: 'baseline',
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      marginBottom: 2 * unit,
      marginTop: unit,
    },
    button: {
      color: 'inherit !important',
      textDecoration: 'none !important',
    },
  })),
  ({ match: { params: { bucket, path } }, classes, signer }) => (
    <React.Fragment>
      <div className={classes.topBar}>
        <BreadCrumbs bucket={bucket} path={path} />
        {!isDir(path) && (
          <Button
            variant="outlined"
            href={signer.getSignedS3URL({ bucket, key: path })}
            className={classes.button}
          >
            Download file
          </Button>
        )}
      </div>

      {isDir(path)
        ? (
          <React.Fragment>
            <Listing bucket={bucket} path={path} />
            <Summary bucket={bucket} path={path} />
          </React.Fragment>
        )
        : (
          <Card>
            <CardContent>
              <ContentWindow handle={{ bucket, key: path }} />
            </CardContent>
          </Card>
        )
      }
    </React.Fragment>
  ));