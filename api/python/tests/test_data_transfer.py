""" Testing for data_transfer.py """

### Python imports

# Backports
try: import pathlib2 as pathlib
except ImportError: import pathlib

try: import unittest.mock as mock
except ImportError: import mock

### Third-party imports
from botocore.stub import ANY, Stubber
import pandas as pd
import pytest

### Project imports
from t4 import data_transfer

### Code

# parquet test moved to test_formats.py

DATA_DIR = pathlib.Path(__file__).parent / 'data'


def test_select():
    # Note: The boto3 Stubber doesn't work properly with s3_client.select_object_content().
    #       The return value expects a dict where an iterable is in the actual results.
    chunks = [
        b'{"foo": ',
        b'9, "b',
        b'ar": 3',
        b'}\n{"foo"',
        b': 9, "bar": 1}\n{"foo": 6, "bar": 9}\n{"foo":',
        b' 1, "bar": 7}\n{"foo":',
        b' 6, "bar": 1}\n{"foo": 6, "bar": 6}',
        b'\n{"foo": 9, "bar": 6}',
        b'\n{"foo": 6, "bar": 4}\n',
        b'{"foo": 2, "bar": 0}',
        b'\n{"foo": 2, "bar": 0}\n',
        ]
    records = [{'Records': {'Payload': chunk}} for chunk in chunks]
    # noinspection PyTypeChecker
    records.append({'Stats': {
        'BytesScanned': 100,
        'BytesProcessed': 100,
        'BytesReturned': 210,
        }})
    records.append({'End': {}})

    expected_result = pd.DataFrame.from_records([
        {'foo': 9, 'bar': 3},
        {'foo': 9, 'bar': 1},
        {'foo': 6, 'bar': 9},
        {'foo': 1, 'bar': 7},
        {'foo': 6, 'bar': 1},
        {'foo': 6, 'bar': 6},
        {'foo': 9, 'bar': 6},
        {'foo': 6, 'bar': 4},
        {'foo': 2, 'bar': 0},
        {'foo': 2, 'bar': 0},
        ])

    # test normal use from extension
    expected_args = {
        'Bucket': 'foo',
        'Key': 'bar/baz.json',
        'Expression': 'select * from S3Object',
        'ExpressionType': 'SQL',
        'InputSerialization': {
            'CompressionType': 'NONE',
            'JSON': {'Type': 'DOCUMENT'}
            },
        'OutputSerialization': {'JSON': {}},
        }
    boto_return_val = {'Payload': iter(records)}
    patched_s3 = mock.patch.object(
        data_transfer.s3_client,
        'select_object_content',
        return_value=boto_return_val,
        autospec=True,
    )
    with patched_s3 as patched:
        result = data_transfer.select('s3://foo/bar/baz.json', 'select * from S3Object')

        patched.assert_called_once_with(**expected_args)
        assert result.equals(expected_result)

    # test no format specified
    patched_s3 = mock.patch.object(
        data_transfer.s3_client,
        'select_object_content',
        autospec=True,
    )
    with patched_s3:
        # No format determined.
        with pytest.raises(data_transfer.QuiltException):
            result = data_transfer.select('s3://foo/bar/baz', 'select * from S3Object')

    # test format-specified in metadata
    expected_args = {
        'Bucket': 'foo',
        'Key': 'bar/baz',
        'Expression': 'select * from S3Object',
        'ExpressionType': 'SQL',
        'InputSerialization': {
            'CompressionType': 'NONE',
            'JSON': {'Type': 'DOCUMENT'}
        },
        'OutputSerialization': {'JSON': {}},
    }

    boto_return_val = {'Payload': iter(records)}
    patched_s3 = mock.patch.object(
        data_transfer.s3_client,
        'select_object_content',
        return_value=boto_return_val,
        autospec=True,
    )
    with patched_s3 as patched:
        result = data_transfer.select('s3://foo/bar/baz', 'select * from S3Object', meta={'target': 'json'})
        assert result.equals(expected_result)
        patched.assert_called_once_with(**expected_args)

    # test compression is specified
    expected_args = {
        'Bucket': 'foo',
        'Key': 'bar/baz.json.gz',
        'Expression': 'select * from S3Object',
        'ExpressionType': 'SQL',
        'InputSerialization': {
            'CompressionType': 'GZIP',
            'JSON': {'Type': 'DOCUMENT'}
            },
        'OutputSerialization': {'JSON': {}},
        }
    boto_return_val = {'Payload': iter(records)}
    patched_s3 = mock.patch.object(
        data_transfer.s3_client,
        'select_object_content',
        return_value=boto_return_val,
        autospec=True,
    )
    with patched_s3 as patched:
        # result ignored -- returned data isn't compressed, and this has already been tested.
        data_transfer.select('s3://foo/bar/baz.json.gz', 'select * from S3Object')
        patched.assert_called_once_with(**expected_args)

def test_get_size_and_meta_no_version():
    stubber = Stubber(data_transfer.s3_client)
    response = {
        'ETag': '12345',
        'VersionId': '1.0',
        'ContentLength': 123,
        'Metadata': {}
    }
    expected_params = {
        'Bucket': 'my_bucket',
        'Key': 'my_obj',
    }
    stubber.add_response('head_object', response, expected_params)

    with stubber:
        # Verify the verion is present
        assert data_transfer.get_size_and_meta('s3://my_bucket/my_obj')[2] == '1.0'

def test_list_local_url():
    dir_path = DATA_DIR / 'dir'
    contents = set(list(data_transfer.list_url(dir_path.as_uri())))
    assert contents == set([
        ('foo.txt', 4),
        ('x/blah.txt', 6)
    ])

def test_etag():
    assert data_transfer._calculate_etag(DATA_DIR / 'small_file.csv') == '"0bec5bf6f93c547bc9c6774acaf85e1a"'
    assert data_transfer._calculate_etag(DATA_DIR / 'buggy_parquet.parquet') == '"dfb5aca048931d396f4534395617363f"'


def test_simple_upload():
    stubber = Stubber(data_transfer.s3_client)

    path = DATA_DIR / 'small_file.csv'

    # Unversioned bucket
    stubber.add_response(
        method='put_object',
        service_response={
            'VersionId': 'null'
        },
        expected_params={
            'Body': ANY,
            'Bucket': 'example',
            'Key': 'foo.csv',
            'Metadata': {'helium': '{}'}
        }
    )

    with stubber:
        data_transfer.copy_file(path.as_uri(), 's3://example/foo.csv')

    stubber.assert_no_pending_responses()

def test_multi_upload():
    stubber = Stubber(data_transfer.s3_client)

    path1 = DATA_DIR / 'small_file.csv'
    path2 = DATA_DIR / 'dir/foo.txt'

    # Unversioned bucket
    stubber.add_response(
        method='put_object',
        service_response={
            'VersionId': 'null'
        },
        expected_params={
            'Body': ANY,
            'Bucket': 'example1',
            'Key': 'foo.csv',
            'Metadata': {'helium': '{}'}
        }
    )

    # Versioned bucket
    stubber.add_response(
        method='put_object',
        service_response={
            'VersionId': 'v123'
        },
        expected_params={
            'Body': ANY,
            'Bucket': 'example2',
            'Key': 'foo.txt',
            'Metadata': {'helium': '{"foo": "bar"}'}
        }
    )

    with stubber:
        # stubber expects responses in order, so disable multi-threading.
        with mock.patch('t4.data_transfer.s3_threads', 1):
          urls = data_transfer.copy_file_list([
              (path1.as_uri(), 's3://example1/foo.csv', path1.stat().st_size, None),
              (path2.as_uri(), 's3://example2/foo.txt', path2.stat().st_size, {'foo': 'bar'}),
          ])

        assert urls[0] == 's3://example1/foo.csv'
        assert urls[1] == 's3://example2/foo.txt?versionId=v123'

    stubber.assert_no_pending_responses()


def test_upload_large_file():
    stubber = Stubber(data_transfer.s3_client)

    path = DATA_DIR / 'large_file.npy'

    stubber.add_client_error(
        method='head_object',
        http_status_code=404,
        expected_params={
            'Bucket': 'example',
            'Key': 'large_file.npy',
        }
    )

    stubber.add_response(
        method='put_object',
        service_response={
            'VersionId': 'v1'
        },
        expected_params={
            'Body': ANY,
            'Bucket': 'example',
            'Key': 'large_file.npy',
            'Metadata': {'helium': '{}'}
        }
    )

    with stubber:
        urls = data_transfer.copy_file_list([
            (path.as_uri(), 's3://example/large_file.npy', path.stat().st_size, None),
        ])
        assert urls[0] == 's3://example/large_file.npy?versionId=v1'

    stubber.assert_no_pending_responses()


def test_upload_large_file_etag_match():
    stubber = Stubber(data_transfer.s3_client)

    path = DATA_DIR / 'large_file.npy'

    stubber.add_response(
        method='head_object',
        service_response={
            'ContentLength': path.stat().st_size,
            'ETag': data_transfer._calculate_etag(path),
            'VersionId': 'v1'
        },
        expected_params={
            'Bucket': 'example',
            'Key': 'large_file.npy',
        }
    )

    with stubber:
        urls = data_transfer.copy_file_list([
            (path.as_uri(), 's3://example/large_file.npy', path.stat().st_size, None),
        ])
        assert urls[0] == 's3://example/large_file.npy?versionId=v1'

    stubber.assert_no_pending_responses()


def test_upload_large_file_etag_mismatch():
    stubber = Stubber(data_transfer.s3_client)

    path = DATA_DIR / 'large_file.npy'

    stubber.add_response(
        method='head_object',
        service_response={
            'ContentLength': path.stat().st_size,
            'ETag': '"123"',
            'VersionId': 'v1'
        },
        expected_params={
            'Bucket': 'example',
            'Key': 'large_file.npy',
        }
    )

    stubber.add_response(
        method='put_object',
        service_response={
            'VersionId': 'v2'
        },
        expected_params={
            'Body': ANY,
            'Bucket': 'example',
            'Key': 'large_file.npy',
            'Metadata': {'helium': '{}'}
        }
    )

    with stubber:
        urls = data_transfer.copy_file_list([
            (path.as_uri(), 's3://example/large_file.npy', path.stat().st_size, None),
        ])
        assert urls[0] == 's3://example/large_file.npy?versionId=v2'

    stubber.assert_no_pending_responses()


def test_upload_large_file_etag_match_metadata():
    stubber = Stubber(data_transfer.s3_client)

    path = DATA_DIR / 'large_file.npy'
    etag = data_transfer._calculate_etag(path)

    stubber.add_response(
        method='head_object',
        service_response={
            'ContentLength': path.stat().st_size,
            'ETag': etag,
            'VersionId': 'v1'
        },
        expected_params={
            'Bucket': 'example',
            'Key': 'large_file.npy',
        }
    )

    stubber.add_response(
        method='copy_object',
        service_response={
            'VersionId': 'v2'
        },
        expected_params={
            'CopySource': {
                'Bucket': 'example',
                'Key': 'large_file.npy',
                'VersionId': 'v1'
            },
            'CopySourceIfMatch': etag,
            'Bucket': 'example',
            'Key': 'large_file.npy',
            'Metadata': {'helium': '{"foo": "bar"}'},
            'MetadataDirective': 'REPLACE'
        }
    )

    with stubber:
        urls = data_transfer.copy_file_list([
            (path.as_uri(), 's3://example/large_file.npy', path.stat().st_size, {'foo': 'bar'}),
        ])
        assert urls[0] == 's3://example/large_file.npy?versionId=v2'

    stubber.assert_no_pending_responses()
