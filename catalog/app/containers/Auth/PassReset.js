import get from 'lodash/fp/get';
import React from 'react';
import { FormattedMessage as FM } from 'react-intl';
import {
  branch,
  renderComponent,
  withStateHandlers,
} from 'recompose';
import { reduxForm, Field, SubmissionError } from 'redux-form/immutable';

import * as NamedRoutes from 'utils/NamedRoutes';
import Link from 'utils/StyledLink';
import defer from 'utils/defer';
import { captureError } from 'utils/errorReporting';
import { composeComponent } from 'utils/reactTools';
import * as validators from 'utils/validators';

import { resetPassword } from './actions';
import msg from './messages';
import * as Layout from './Layout';


const Container = Layout.mkLayout(<FM {...msg.passResetHeading} />);

// TODO: what to show if user is authenticated?
export default composeComponent('Auth.PassReset',
  // connect(createStructuredSelector({ authenticated })),
  withStateHandlers({
    done: false,
  }, {
    setDone: () => () => ({ done: true }),
  }),
  reduxForm({
    form: 'Auth.PassReset',
    onSubmit: async (values, dispatch, { setDone }) => {
      try {
        const result = defer();
        dispatch(resetPassword(values.toJS().email, result.resolver));
        await result.promise;
        setDone();
      } catch (e) {
        captureError(e);
        throw new SubmissionError({ _error: 'unexpected' });
      }
    },
  }),
  branch(get('done'), renderComponent(() => (
    <Container>
      <Layout.Message>
        <FM {...msg.passResetSuccess} />
      </Layout.Message>
    </Container>
  ))),
  ({ handleSubmit, submitting, submitFailed, invalid, error }) => {
    const { urls } = NamedRoutes.use();
    return (
      <Container>
        <form onSubmit={handleSubmit}>
          <Field
            component={Layout.Field}
            name="email"
            validate={[validators.required]}
            disabled={submitting}
            floatingLabelText={<FM {...msg.passResetEmailLabel} />}
            errors={{
              required: <FM {...msg.passResetEmailRequired} />,
            }}
          />
          <Layout.Error
            {...{ submitFailed, error }}
            errors={{
              unexpected: <FM {...msg.passResetErrorUnexpected} />,
            }}
          />
          <Layout.Actions>
            <Layout.Submit
              label={<FM {...msg.passResetSubmit} />}
              disabled={submitting || (submitFailed && invalid)}
              busy={submitting}
            />
          </Layout.Actions>
          <Layout.Hint>
            <FM
              {...msg.passResetHintSignUp}
              values={{
                link: (
                  <Link to={urls.signUp()}>
                    <FM {...msg.passResetHintSignUpLink} />
                  </Link>
                ),
              }}
            />
          </Layout.Hint>
        </form>
      </Container>
    );
  });
