#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import gzip
from io import BytesIO


class ZipStream(object):
    """Zip a stream that yields binary data"""

    def __init__(self, stream, get_chunk_method):
        """
        - stream: the input stream
        - get_chunk_method: name of the method to get a chunk of the stream
        """
        self.stream = stream
        self.buffer = BytesIO()
        self.zipfile = gzip.GzipFile(mode='wb', fileobj=self.buffer)
        self.get_chunk = getattr(self.stream, get_chunk_method)

    def __next__(self):
        line = self.get_chunk()
        if not len(line):
            raise StopIteration
        self.zipfile.write(line)
        self.zipfile.flush()
        zipped = self.buffer.getvalue()
        self.buffer.truncate(0)
        self.buffer.seek(0)
        return zipped

    def __iter__(self):
        return self
