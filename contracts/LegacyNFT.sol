// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * LegacyNFT — ERC-721 for Micro-Legacy geo drops.
 * Each NFT represents a Legacy dropped by a user in the real world.
 * Metadata (content, lat/lng, city) is stored as a tokenURI (IPFS).
 */
contract LegacyNFT is ERC721, ERC721URIStorage, Ownable {
    uint256 private _nextTokenId;

    event LegacyMinted(uint256 indexed tokenId, address indexed to, uint256 legacyId);

    constructor() ERC721("GOAT Legacy", "LEGACY") Ownable(msg.sender) {}

    function mint(address to, string calldata tokenURI_, uint256 legacyId)
        external
        onlyOwner
        returns (uint256)
    {
        uint256 tokenId = ++_nextTokenId;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);
        emit LegacyMinted(tokenId, to, legacyId);
        return tokenId;
    }

    function totalMinted() external view returns (uint256) {
        return _nextTokenId;
    }

    // Required overrides
    function tokenURI(uint256 tokenId)
        public view override(ERC721, ERC721URIStorage) returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC721URIStorage) returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
