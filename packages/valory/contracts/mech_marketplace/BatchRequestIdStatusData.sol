// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

enum RequestStatus {
    DoesNotExist,
    RequestedPriority,
    RequestedExpired,
    Delivered
}

interface IMechMarketplace {
    function getRequestStatus(
        bytes32 requestId
    ) external view returns (RequestStatus status);
}

//This contract is used to fetch multiple request ids status from the MechMarketplace contract
contract BatchRequestIdStatusData {
    // definition of the batching input data
    constructor(IMechMarketplace _marketplace, bytes32[] memory _requestIds) {
        // cache requestIds length
        uint256 requestIdsLength = _requestIds.length;

        // create temporary array with requestIds length to populate only with requestIds that have status 1 or 2
        bytes32[] memory tempRequestIds = new bytes32[](requestIdsLength);

        // declare counter to know how many of the request are eligible
        uint256 eligibleRequestIdsCount;

        for (uint256 _i; _i < requestIdsLength; ) {
            RequestStatus status = _marketplace.getRequestStatus(
                _requestIds[_i]
            );
            if (
                status == RequestStatus.RequestedPriority ||
                status == RequestStatus.RequestedExpired
            ) {
                tempRequestIds[eligibleRequestIdsCount] = _requestIds[_i];
                ++eligibleRequestIdsCount;
            }

            unchecked {
                ++_i;
            }
        }

        // create a new array with the actual length of the eligible to not corrupt memory with a wrong length
        bytes32[] memory eligibleRequestIds = new bytes32[](
            eligibleRequestIdsCount
        );

        // populate the array with the eligible requestIds
        for (uint256 _i; _i < eligibleRequestIdsCount; ) {
            eligibleRequestIds[_i] = tempRequestIds[_i];
            unchecked {
                ++_i;
            }
        }

        // encode the return data
        bytes memory _data = abi.encode(eligibleRequestIds);

        // force the constructor to return data via assembly
        assembly {
            // abi.encode adds offset (32 bytes) that we need to skip
            let _dataStart := add(_data, 32)
            // msize() gets the size of active memory in bytes.
            // if we subtract msize() from _dataStart, the output will be
            // the number of bytes from _dataStart to the end of memory
            // which, due to how the data has been laid out in memory, will coincide with
            // where our desired data ends.
            let _dataEnd := sub(msize(), _dataStart)
            // starting from _dataStart, get all the data in memory.
            return(_dataStart, _dataEnd)
        }
    }
}
